using Microsoft.Win32;

namespace AcDbPlugin.Data
{
    /// <summary>
    /// Persists plugin settings under HKCU\Software\AcDbPlugin.
    /// </summary>
    public static class PluginSettings
    {
        private const string RegKey = @"Software\AcDbPlugin";

        public static string DatabasePath
        {
            get
            {
                using var key = Registry.CurrentUser.OpenSubKey(RegKey);
                return key?.GetValue("DatabasePath") as string ?? string.Empty;
            }
            set
            {
                using var key = Registry.CurrentUser.CreateSubKey(RegKey);
                key.SetValue("DatabasePath", value ?? string.Empty);
            }
        }
    }
}
