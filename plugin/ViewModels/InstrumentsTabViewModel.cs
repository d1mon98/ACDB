using System;
using System.Collections.ObjectModel;
using System.Threading.Tasks;
using AcDbPlugin.Data;

namespace AcDbPlugin.ViewModels
{
    public class InstrumentsTabViewModel : ViewModelBase
    {
        private readonly MainViewModel _main;
        private Instrument? _selected;

        public InstrumentsTabViewModel(MainViewModel main)
        {
            _main = main;
            RefreshCommand       = new AsyncRelayCommand(LoadAsync);
            AddCommand           = new AsyncRelayCommand(AddAsync);
            EditCommand          = new AsyncRelayCommand(EditAsync,   () => _selected != null);
            DeleteCommand        = new AsyncRelayCommand(DeleteAsync, () => _selected != null);
            InsertDrawingCommand = new RelayCommand(InsertIntoDrawing, () => _selected != null);
        }

        public ObservableCollection<Instrument> Rows { get; } = new ObservableCollection<Instrument>();

        public Instrument? Selected { get => _selected; set => Set(ref _selected, value); }

        public AsyncRelayCommand RefreshCommand       { get; }
        public AsyncRelayCommand AddCommand           { get; }
        public AsyncRelayCommand EditCommand          { get; }
        public AsyncRelayCommand DeleteCommand        { get; }
        public RelayCommand      InsertDrawingCommand { get; }

        public async Task LoadAsync()
        {
            var proj = _main.SelectedProject;
            if (_main.Db == null || proj == null) { Rows.Clear(); return; }
            _main.IsBusy = true;
            try
            {
                var list = await _main.Db.GetInstrumentsAsync(proj.ProjectId);
                Rows.Clear();
                foreach (var i in list) Rows.Add(i);
            }
            catch (Exception ex) { _main.Status = $"Instruments error: {ex.Message}"; }
            finally { _main.IsBusy = false; }
        }

        private async Task AddAsync()
        {
            var proj = _main.SelectedProject;
            if (_main.Db == null || proj == null) return;

            var vm = new RecordEntryViewModel(RecordType.Instrument, _main.Db, proj.ProjectId);
            await vm.LoadCatalogsAsync();

            var win = new Views.RecordEntryWindow(vm);
            if (win.ShowDialog() != true) return;

            try
            {
                var inst = vm.ToInstrument();
                await _main.Db.AddInstrumentAsync(inst);
                _main.Status = $"Instrument {inst.Tag} added.";
                await LoadAsync();
            }
            catch (Exception ex) { _main.Status = $"Add failed: {ex.Message}"; }
        }

        private async Task EditAsync()
        {
            if (_main.Db == null || _selected == null || _main.SelectedProject == null) return;

            var vm = new RecordEntryViewModel(RecordType.Instrument, _main.Db,
                                              _main.SelectedProject.ProjectId);
            await vm.LoadCatalogsAsync();
            vm.LoadInstrument(_selected);

            var win = new Views.RecordEntryWindow(vm);
            if (win.ShowDialog() != true) return;

            try
            {
                var inst = vm.ToInstrument();
                inst.InstrumentId = _selected.InstrumentId;
                inst.ProjectId    = _selected.ProjectId;
                await _main.Db.UpdateInstrumentAsync(inst);
                _main.Status = $"Instrument {inst.Tag} updated.";
                await LoadAsync();
            }
            catch (Exception ex) { _main.Status = $"Edit failed: {ex.Message}"; }
        }

        private async Task DeleteAsync()
        {
            if (_main.Db == null || _selected == null) return;
            var r = System.Windows.MessageBox.Show(
                $"Delete instrument '{_selected.Tag}'?", "Confirm Delete",
                System.Windows.MessageBoxButton.YesNo,
                System.Windows.MessageBoxImage.Warning);
            if (r != System.Windows.MessageBoxResult.Yes) return;

            try
            {
                await _main.Db.DeleteInstrumentAsync(_selected.InstrumentId);
                _main.Status = $"Instrument {_selected.Tag} deleted.";
                await LoadAsync();
            }
            catch (Exception ex) { _main.Status = $"Delete failed: {ex.Message}"; }
        }

        private void InsertIntoDrawing()
        {
            if (_selected == null) return;
            Integration.DrawingIntegration.InsertInstrument(_selected);
        }
    }
}
