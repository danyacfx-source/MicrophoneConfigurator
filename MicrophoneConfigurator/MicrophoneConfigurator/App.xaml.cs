using System;
using System.IO;
using System.Windows;
using System.Windows.Threading;
using MicrophoneConfigurator.Core;

namespace MicrophoneConfigurator
{
    public partial class App : Application
    {
        public static AudioEngine AudioEngine { get; private set; } = null!;

        protected override void OnStartup(StartupEventArgs e)
        {
            base.OnStartup(e);
            DispatcherUnhandledException += OnDispatcherUnhandledException;
            AppDomain.CurrentDomain.UnhandledException += OnUnhandledException;
            try
            {
                AudioEngine = new AudioEngine();
            }
            catch (Exception ex)
            {
                File.WriteAllText("crash.log", ex.ToString());
            }
        }

        private void OnDispatcherUnhandledException(object sender, DispatcherUnhandledExceptionEventArgs e)
        {
            File.WriteAllText("crash.log", e.Exception.ToString());
            e.Handled = true;
        }

        private void OnUnhandledException(object sender, UnhandledExceptionEventArgs e)
        {
            if (e.ExceptionObject is Exception ex)
                File.WriteAllText("crash.log", ex.ToString());
        }

        protected override void OnExit(ExitEventArgs e)
        {
            AudioEngine?.Dispose();
            base.OnExit(e);
        }
    }
}
