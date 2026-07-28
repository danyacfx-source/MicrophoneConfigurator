using System;
using System.Windows;
using MicrophoneConfigurator.Core;

namespace MicrophoneConfigurator
{
    public partial class App : Application
    {
        public static AudioEngine AudioEngine { get; private set; } = null!;

        protected override void OnStartup(StartupEventArgs e)
        {
            base.OnStartup(e);
            AudioEngine = new AudioEngine();
        }

        protected override void OnExit(ExitEventArgs e)
        {
            AudioEngine?.Dispose();
            base.OnExit(e);
        }
    }
}
