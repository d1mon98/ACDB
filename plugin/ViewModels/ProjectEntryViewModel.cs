using System;
using System.Collections.Generic;
using AcDbPlugin.Data;

namespace AcDbPlugin.ViewModels
{
    public class ProjectEntryViewModel : ViewModelBase
    {
        private string _projectNumber = "";
        private string _projectName   = "";
        private string _client        = "";
        private string _location      = "";
        private string _engineer      = "";
        private string _necEdition    = "2023";
        private string _voltageSystem = "";
        private string _notes         = "";
        private string _issueDate     = "";

        public string ProjectNumber  { get => _projectNumber; set => Set(ref _projectNumber, value); }
        public string ProjectName    { get => _projectName;   set => Set(ref _projectName, value); }
        public string Client         { get => _client;        set => Set(ref _client, value); }
        public string Location       { get => _location;      set => Set(ref _location, value); }
        public string Engineer       { get => _engineer;      set => Set(ref _engineer, value); }
        public string NecEdition     { get => _necEdition;    set => Set(ref _necEdition, value); }
        public string VoltageSystem  { get => _voltageSystem; set => Set(ref _voltageSystem, value); }
        public string Notes          { get => _notes;         set => Set(ref _notes, value); }
        public string IssueDate      { get => _issueDate;     set => Set(ref _issueDate, value); }

        public List<string> NecEditions { get; } =
            new List<string> { "2023", "2020", "2017", "2014" };

        public void LoadProject(Project p)
        {
            ProjectNumber = p.ProjectNumber ?? "";
            ProjectName   = p.ProjectName   ?? "";
            Client        = p.Client        ?? "";
            Location      = p.Location      ?? "";
            Engineer      = p.EngineerOfRecord ?? "";
            NecEdition    = p.NecEdition    ?? "2023";
            VoltageSystem = p.VoltageSystem ?? "";
            Notes         = p.Notes         ?? "";
            IssueDate     = p.IssueDate.HasValue
                ? p.IssueDate.Value.ToString("yyyy-MM-dd") : "";
        }

        public Project ToProject() => new Project
        {
            ProjectNumber    = ProjectNumber.Trim(),
            ProjectName      = ProjectName.Trim(),
            Client           = Client.Trim(),
            Location         = Location.Trim(),
            EngineerOfRecord = Engineer.Trim(),
            NecEdition       = NecEdition.Trim(),
            VoltageSystem    = VoltageSystem.Trim(),
            Notes            = Notes.Trim(),
            IssueDate        = DateTime.TryParse(IssueDate, out var dt) ? dt : (DateTime?)null,
        };
    }
}
