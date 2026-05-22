using System;
using System.Collections.ObjectModel;
using System.Threading.Tasks;
using System.Windows;
using AcDbPlugin.Data;
using AcDbPlugin.Integration;
using AcApp = Autodesk.AutoCAD.ApplicationServices.Application;

namespace AcDbPlugin.ViewModels
{
    /// <summary>
    /// Root ViewModel for the palette. Owns the active project and all tab VMs.
    /// </summary>
    public class MainViewModel : ViewModelBase
    {
        private DbContext? _db;
        private Project? _selectedProject;
        private string _status = "No database loaded.";
        private bool _isBusy;

        // ── Poller state ──────────────────────────────────────────────────────
        private bool _pollerEnabled;
        private int _pollerIntervalSeconds = 10;
        private System.Timers.Timer? _pollTimer;
        private DateTime _lastDbWriteTime = DateTime.MinValue;

        public ObservableCollection<Project> Projects { get; } = new ObservableCollection<Project>();

        public CatalogTabViewModel    Catalogs    { get; }
        public EquipmentTabViewModel  Equipment   { get; }
        public InstrumentsTabViewModel Instruments { get; }
        public CablesTabViewModel     Cables      { get; }

        public Project? SelectedProject
        {
            get => _selectedProject;
            set
            {
                if (Set(ref _selectedProject, value))
                    _ = OnProjectChangedAsync();
            }
        }

        public string Status  { get => _status;  set => Set(ref _status, value); }
        public bool   IsBusy  { get => _isBusy;  set => Set(ref _isBusy, value); }

        public AsyncRelayCommand LoadProjectsCommand  { get; }
        public AsyncRelayCommand AddProjectCommand   { get; }
        public AsyncRelayCommand EditProjectCommand  { get; }
        public AsyncRelayCommand DeleteProjectCommand{ get; }
        public RelayCommand      SetDatabaseCommand  { get; }
        public RelayCommand      SyncLinkedCommand   { get; }

        /// <summary>
        /// Toggles the background poller. When enabled, the poller checks the DB
        /// file's last-write-time every PollerIntervalSeconds seconds and calls
        /// RefreshAll if the file has changed. This is polling — not a live push.
        /// </summary>
        public bool PollerEnabled
        {
            get => _pollerEnabled;
            set
            {
                if (!Set(ref _pollerEnabled, value)) return;
                if (value) StartPoller();
                else StopPoller();
            }
        }

        public int PollerIntervalSeconds
        {
            get => _pollerIntervalSeconds;
            set
            {
                if (value < 1) value = 1;
                if (!Set(ref _pollerIntervalSeconds, value)) return;
                if (_pollerEnabled) { StopPoller(); StartPoller(); }
            }
        }

        public MainViewModel()
        {
            Catalogs     = new CatalogTabViewModel(this);
            Equipment    = new EquipmentTabViewModel(this);
            Instruments  = new InstrumentsTabViewModel(this);
            Cables       = new CablesTabViewModel(this);

            LoadProjectsCommand   = new AsyncRelayCommand(LoadProjectsAsync);
            AddProjectCommand     = new AsyncRelayCommand(AddProjectAsync);
            EditProjectCommand    = new AsyncRelayCommand(EditProjectAsync,   () => _selectedProject != null);
            DeleteProjectCommand  = new AsyncRelayCommand(DeleteProjectAsync, () => _selectedProject != null);
            SetDatabaseCommand    = new RelayCommand(PromptForDatabase);
            SyncLinkedCommand     = new RelayCommand(SyncLinked);

            // Auto-load if a path was already saved
            var savedPath = PluginSettings.DatabasePath;
            if (!string.IsNullOrEmpty(savedPath))
                _ = InitDatabaseAsync(savedPath);
        }

        public DbContext? Db => _db;

        public async Task InitDatabaseAsync(string path)
        {
            try
            {
                _db = new DbContext(path);
                PluginSettings.DatabasePath = path;
                Status = $"DB: {System.IO.Path.GetFileName(path)}";
                await LoadProjectsAsync();
            }
            catch (Exception ex)
            {
                Status = $"Error opening DB: {ex.Message}";
                _db = null;
            }
        }

        private async Task LoadProjectsAsync()
        {
            if (_db == null) return;
            IsBusy = true;
            Status = "Loading projects...";
            try
            {
                var list = await _db.GetProjectsAsync();
                Projects.Clear();
                foreach (var p in list) Projects.Add(p);
                Status = list.Count == 0
                    ? "No projects found. Use the Python CLI to create one."
                    : $"Loaded {list.Count} project(s).";
            }
            catch (Exception ex)
            {
                Status = $"Error: {ex.Message}";
            }
            finally { IsBusy = false; }
        }

        private async Task OnProjectChangedAsync()
        {
            if (SelectedProject == null) return;
            await Task.WhenAll(
                Equipment.LoadAsync(),
                Instruments.LoadAsync(),
                Cables.LoadAsync());
        }

        private async Task AddProjectAsync()
        {
            if (_db == null) { Status = "Open a database first."; return; }
            var vm  = new ProjectEntryViewModel();
            var win = new Views.ProjectEntryWindow(vm, "New Project");
            if (win.ShowDialog() != true) return;
            var proj = vm.ToProject();
            if (string.IsNullOrWhiteSpace(proj.ProjectNumber))
            { Status = "Project Number is required."; return; }
            try
            {
                await _db.AddProjectAsync(proj);
                Status = $"Project {proj.ProjectNumber} created.";
                await LoadProjectsAsync();
                SelectedProject = Projects.Count > 0
                    ? Projects[Projects.Count - 1] : null;
            }
            catch (Exception ex) { Status = $"Add failed: {ex.Message}"; }
        }

        private async Task EditProjectAsync()
        {
            if (_db == null || _selectedProject == null) return;
            var vm  = new ProjectEntryViewModel();
            vm.LoadProject(_selectedProject);
            var win = new Views.ProjectEntryWindow(vm, "Edit Project");
            if (win.ShowDialog() != true) return;
            var proj = vm.ToProject();
            proj.ProjectId = _selectedProject.ProjectId;
            if (string.IsNullOrWhiteSpace(proj.ProjectNumber))
            { Status = "Project Number is required."; return; }
            try
            {
                await _db.UpdateProjectAsync(proj);
                Status = $"Project {proj.ProjectNumber} updated.";
                await LoadProjectsAsync();
            }
            catch (Exception ex) { Status = $"Edit failed: {ex.Message}"; }
        }

        private async Task DeleteProjectAsync()
        {
            if (_db == null || _selectedProject == null) return;
            var r = MessageBox.Show(
                $"Delete project '{_selectedProject.ProjectNumber}'?\nThis will also delete all equipment, instruments, and cables in this project.",
                "Confirm Delete", MessageBoxButton.YesNo, MessageBoxImage.Warning);
            if (r != MessageBoxResult.Yes) return;
            try
            {
                await _db.DeleteProjectAsync(_selectedProject.ProjectId);
                Status = "Project deleted.";
                await LoadProjectsAsync();
            }
            catch (Exception ex) { Status = $"Delete failed: {ex.Message}"; }
        }

        private void SyncLinked()
        {
            if (_db == null) { Status = "No database loaded."; return; }
            var doc = AcApp.DocumentManager.MdiActiveDocument;
            if (doc == null) { Status = "No active drawing."; return; }
            try
            {
                var (updated, missing) = LinkedBlockService.RefreshAll(doc, _db);
                Status = $"Sync: {updated} refreshed, {missing} stale.";
            }
            catch (Exception ex) { Status = $"Sync error: {ex.Message}"; }
        }

        private void StartPoller()
        {
            _lastDbWriteTime = _db?.GetDbLastModified() ?? DateTime.MinValue;
            _pollTimer = new System.Timers.Timer(_pollerIntervalSeconds * 1000)
            {
                AutoReset = true,
            };
            _pollTimer.Elapsed += OnPollTick;
            _pollTimer.Start();
        }

        private void StopPoller()
        {
            _pollTimer?.Stop();
            _pollTimer?.Dispose();
            _pollTimer = null;
        }

        // Called on a timer thread — dispatch drawing work to the AutoCAD main context.
        private void OnPollTick(object sender, System.Timers.ElapsedEventArgs e)
        {
            if (_db == null) return;
            var writeTime = _db.GetDbLastModified();
            if (writeTime <= _lastDbWriteTime) return;
            _lastDbWriteTime = writeTime;

            AcApp.DocumentManager.ExecuteInApplicationContext(
                _ =>
                {
                    try
                    {
                        var doc = AcApp.DocumentManager.MdiActiveDocument;
                        if (doc == null) return;
                        var (updated, missing) = LinkedBlockService.RefreshAll(doc, _db);
                        // Marshal the status update back to the WPF dispatcher.
                        System.Windows.Application.Current?.Dispatcher.Invoke(
                            () => Status = $"Auto-sync: {updated} refreshed, {missing} stale.");
                    }
                    catch
                    {
                        // Silently skip if the drawing is busy (another command active).
                    }
                },
                null);
        }

        private void PromptForDatabase()
        {
            var dlg = new Microsoft.Win32.OpenFileDialog
            {
                Title  = "Select Electrical Project Database",
                Filter = "SQLite Database (*.db)|*.db|All files (*.*)|*.*",
            };
            var saved = PluginSettings.DatabasePath;
            if (!string.IsNullOrEmpty(saved))
                dlg.InitialDirectory = System.IO.Path.GetDirectoryName(saved);

            if (dlg.ShowDialog() == true)
                _ = InitDatabaseAsync(dlg.FileName);
        }
    }
}
