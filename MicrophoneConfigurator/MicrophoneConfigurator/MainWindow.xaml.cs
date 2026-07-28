using System;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Data;
using System.Windows.Media.Effects;
using System.Windows.Input;
using System.Windows.Media;
using System.Windows.Threading;
using System.Windows.Controls.Primitives;
using Hardcodet.Wpf.TaskbarNotification;
using MicrophoneConfigurator.ViewModels;

namespace MicrophoneConfigurator
{
    public partial class MainWindow : Window
    {
        private MainViewModel _viewModel;
        private DispatcherTimer _visualizationTimer;
        private float[] _smoothedSpectrum;
        private float[] _peakHold;
        private DispatcherTimer _peakDecayTimer;
        private TaskbarIcon? _trayIcon;

        public MainWindow()
        {
            InitializeComponent();

            _viewModel = new MainViewModel(App.AudioEngine);
            DataContext = _viewModel;

            _smoothedSpectrum = new float[64];
            _peakHold = new float[64];

            _viewModel.AudioDataUpdated += OnAudioDataUpdated;

            _visualizationTimer = new DispatcherTimer { Interval = TimeSpan.FromMilliseconds(30) };
            _visualizationTimer.Tick += (s, e) => RedrawVisualization();
            _visualizationTimer.Start();

            _peakDecayTimer = new DispatcherTimer { Interval = TimeSpan.FromMilliseconds(100) };
            _peakDecayTimer.Tick += (s, e) => DecayPeaks();
            _peakDecayTimer.Start();

            Loaded += (s, e) =>
            {
                _viewModel.RefreshDevicesCommand.Execute(null);

                if (_viewModel.Settings.WindowLeft >= 0 && _viewModel.Settings.WindowTop >= 0)
                {
                    Left = _viewModel.Settings.WindowLeft;
                    Top = _viewModel.Settings.WindowTop;
                }
                Width = _viewModel.Settings.WindowWidth;
                Height = _viewModel.Settings.WindowHeight;

                InitTrayIcon();
            };
        }

        private void InitTrayIcon()
        {
            _trayIcon = new TaskbarIcon
            {
                ToolTipText = "MicStudio Pro",
                Visibility = Visibility.Visible,
            };

            _trayIcon.DoubleClickCommand = _viewModel.StartMonitoringCommand;

            var contextMenu = new ContextMenu();

            var showItem = new MenuItem { Header = "Показать" };
            showItem.Click += ShowWindow_Click;
            contextMenu.Items.Add(showItem);

            contextMenu.Items.Add(new Separator());

            var listenItem = new MenuItem { Header = "Слушать" };
            listenItem.Command = _viewModel.StartMonitoringCommand;
            contextMenu.Items.Add(listenItem);

            var stopItem = new MenuItem { Header = "Стоп" };
            stopItem.Command = _viewModel.StopMonitoringCommand;
            contextMenu.Items.Add(stopItem);

            contextMenu.Items.Add(new Separator());

            var exitItem = new MenuItem { Header = "Выход" };
            exitItem.Click += ExitApplication_Click;
            contextMenu.Items.Add(exitItem);

            _trayIcon.ContextMenu = contextMenu;
        }

        private void Window_KeyDown(object sender, KeyEventArgs e)
        {
            if (e.Key == Key.Space && Keyboard.Modifiers == ModifierKeys.None)
            {
                if (_viewModel.IsMonitoring) _viewModel.StopMonitoringCommand.Execute(null);
                else _viewModel.StartMonitoringCommand.Execute(null);
                e.Handled = true;
            }
            else if (e.Key == Key.R && Keyboard.Modifiers == ModifierKeys.Control)
            {
                if (_viewModel.IsRecording) _viewModel.StopRecordingCommand.Execute(null);
                else _viewModel.StartRecordingCommand.Execute(null);
                e.Handled = true;
            }
        }

        private void Window_Closing(object sender, System.ComponentModel.CancelEventArgs e)
        {
            _viewModel.Settings.WindowLeft = Left;
            _viewModel.Settings.WindowTop = Top;
            _viewModel.Settings.WindowWidth = Width;
            _viewModel.Settings.WindowHeight = Height;
            _viewModel.Settings.Save();
            _trayIcon?.Dispose();
        }

        private void Window_StateChanged(object sender, EventArgs e)
        {
            if (WindowState == WindowState.Minimized && _viewModel.Settings.MinimizeToTray)
            {
                Hide();
                if (_trayIcon != null) _trayIcon.Visibility = Visibility.Visible;
            }
        }

        private void TitleBar_MouseLeftButtonDown(object sender, MouseButtonEventArgs e)
        {
            if (e.ClickCount == 2)
                WindowState = WindowState == WindowState.Maximized ? WindowState.Normal : WindowState.Maximized;
            else
                DragMove();
        }

        private void MinimizeBtn_Click(object sender, RoutedEventArgs e) => WindowState = WindowState.Minimized;

        private void TrayBtn_Click(object sender, RoutedEventArgs e)
        {
            WindowState = WindowState.Minimized;
            Hide();
            if (_trayIcon != null) _trayIcon.Visibility = Visibility.Visible;
        }

        private void CloseBtn_Click(object sender, RoutedEventArgs e) => Close();

        private void ShowWindow_Click(object sender, RoutedEventArgs e)
        {
            Show();
            WindowState = WindowState.Normal;
            if (_trayIcon != null) _trayIcon.Visibility = Visibility.Collapsed;
        }

        private void ExitApplication_Click(object sender, RoutedEventArgs e)
        {
            _trayIcon?.Dispose();
            Application.Current.Shutdown();
        }

        private void DevicesButton_Click(object sender, RoutedEventArgs e) =>
            _viewModel.RefreshDevicesCommand.Execute(null);

        private void ListenBtn_Click(object sender, RoutedEventArgs e) =>
            _viewModel.StartMonitoringCommand.Execute(null);

        private void StopBtn_Click(object sender, RoutedEventArgs e) =>
            _viewModel.StopMonitoringCommand.Execute(null);

        private void RecordBtn_Click(object sender, RoutedEventArgs e) =>
            _viewModel.StartRecordingCommand.Execute(null);

        private void StopRecordBtn_Click(object sender, RoutedEventArgs e) =>
            _viewModel.StopRecordingCommand.Execute(null);

        private void SaveSlotA_Click(object sender, RoutedEventArgs e) =>
            _viewModel.SaveToACommand.Execute(null);

        private void SaveSlotB_Click(object sender, RoutedEventArgs e) =>
            _viewModel.SaveToBCommand.Execute(null);

        private void ToggleAB_Click(object sender, RoutedEventArgs e) =>
            _viewModel.ToggleABCommand.Execute(null);

        private void ResetEQ_Click(object sender, RoutedEventArgs e) =>
            _viewModel.ResetEqualizerCommand.Execute(null);

        private void LoadEffectPreset_Click(object sender, RoutedEventArgs e) =>
            _viewModel.LoadPresetCommand.Execute(null);

        private void SaveEffectPreset_Click(object sender, RoutedEventArgs e) =>
            _viewModel.SavePresetCommand.Execute(null);

        private void DeleteEffectPreset_Click(object sender, RoutedEventArgs e) =>
            _viewModel.DeletePresetCommand.Execute(null);

        private void ApplyVoicePreset_Click(object sender, RoutedEventArgs e)
        {
            if (sender is Button btn && btn.DataContext is VoicePreset preset)
                _viewModel.ApplyVoicePresetCommand.Execute(preset.Name);
        }

        private void OnAudioDataUpdated()
        {
            Dispatcher.BeginInvoke(() => RedrawVisualization());
        }

        private void RedrawVisualization()
        {
            if (_viewModel == null) return;
            UpdateVuMeter(_viewModel.SpectrumData);
            DrawSpectrum(_viewModel.SpectrumData);
            UpdateGainReduction();
        }

        private void DecayPeaks()
        {
            for (int i = 0; i < _peakHold.Length; i++)
            {
                _peakHold[i] *= 0.93f;
                if (_peakHold[i] < 0.01f) _peakHold[i] = 0;
            }
            if (VuLeftPeak.Height < 0.5) VuLeftPeak.Height = 0;
            if (VuRightPeak.Height < 0.5) VuRightPeak.Height = 0;
        }

        private void UpdateVuMeter(float[] data)
        {
            if (data == null || data.Length == 0) return;

            float level = 0;
            for (int i = 0; i < data.Length; i++) level += data[i];
            level /= data.Length;

            double height = Math.Min(level * 350, 130);
            double db = level > 0 ? 20 * Math.Log10(level) : -60;

            VuLeftBar.Height = height;
            VuRightBar.Height = height * 0.95;

            double peakH = Math.Max(height, VuLeftPeak.Height);
            VuLeftPeak.Height = peakH;
            VuRightPeak.Height = peakH * 0.95;

            VuPeakLabel.Text = $"{db:F0} dB";
            VuPeakLabel.Foreground = db > -6 ? new SolidColorBrush(Colors.Red)
                : db > -18 ? new SolidColorBrush(Color.FromRgb(253, 203, 110))
                : new SolidColorBrush(Color.FromRgb(136, 136, 170));
        }

        private void UpdateGainReduction()
        {
            float gr = _viewModel.GainReduction;
            double normalized = Math.Max(0, Math.Min(1, (-gr) / 30.0));
            GainReductionBar.Width = normalized * 198;
            GainReductionLabel.Text = $"{gr:F1} dB";
        }

        private void DrawSpectrum(float[] data)
        {
            SpectrumCanvas.Children.Clear();
            if (data == null || data.Length == 0) return;

            double canvasWidth = SpectrumCanvas.ActualWidth;
            double canvasHeight = SpectrumCanvas.ActualHeight;
            if (canvasWidth <= 0 || canvasHeight <= 0) return;

            int displayBars = Math.Min(data.Length, 48);
            double barWidth = canvasWidth / displayBars;
            double gap = 2;

            for (int i = 0; i < displayBars && i < data.Length; i++)
            {
                float target = Math.Min(data[i] * 3.5f, 1.0f);
                _smoothedSpectrum[i] += (target - _smoothedSpectrum[i]) * 0.35f;

                if (_smoothedSpectrum[i] > _peakHold[i])
                    _peakHold[i] = _smoothedSpectrum[i];

                double height = Math.Max(_smoothedSpectrum[i] * canvasHeight, 2);
                double peakHeight = Math.Max(_peakHold[i] * canvasHeight, 2);
                double ratio = _smoothedSpectrum[i];

                Color barColor;
                if (ratio < 0.33)
                    barColor = ColorExtensions.Lerp(Color.FromRgb(0, 206, 201), Color.FromRgb(108, 92, 231), ratio * 3);
                else if (ratio < 0.66)
                    barColor = ColorExtensions.Lerp(Color.FromRgb(108, 92, 231), Color.FromRgb(253, 203, 110), (ratio - 0.33f) * 3);
                else
                    barColor = ColorExtensions.Lerp(Color.FromRgb(253, 203, 110), Color.FromRgb(255, 107, 107), (ratio - 0.66f) * 3);

                var bar = new System.Windows.Shapes.Rectangle
                {
                    Width = barWidth - gap,
                    Height = height,
                    RadiusX = 2,
                    RadiusY = 2,
                    Fill = new LinearGradientBrush(barColor, Color.FromArgb(30, barColor.R, barColor.G, barColor.B), 90),
                    Effect = new DropShadowEffect { Color = barColor, BlurRadius = 10, ShadowDepth = 0, Opacity = 0.35 }
                };

                Canvas.SetLeft(bar, i * barWidth + gap / 2);
                Canvas.SetBottom(bar, 0);
                SpectrumCanvas.Children.Add(bar);

                var peakLine = new System.Windows.Shapes.Rectangle
                {
                    Width = barWidth - gap,
                    Height = 2,
                    RadiusX = 1,
                    RadiusY = 1,
                    Fill = new SolidColorBrush(Color.FromArgb(180, 255, 255, 255))
                };
                Canvas.SetLeft(peakLine, i * barWidth + gap / 2);
                Canvas.SetBottom(peakLine, peakHeight);
                SpectrumCanvas.Children.Add(peakLine);
            }
        }
    }

    public static class ColorExtensions
    {
        public static Color Lerp(Color a, Color b, double t)
        {
            t = Math.Clamp(t, 0, 1);
            return Color.FromArgb(
                (byte)(a.A + (b.A - a.A) * t),
                (byte)(a.R + (b.R - a.R) * t),
                (byte)(a.G + (b.G - a.G) * t),
                (byte)(a.B + (b.B - a.B) * t)
            );
        }
    }

    public class VolumeConverter : IValueConverter
    {
        public static readonly VolumeConverter Instance = new();
        public object Convert(object value, Type targetType, object parameter, System.Globalization.CultureInfo culture)
            => value is float vol ? $"{(vol * 100):F0}%" : "100%";
        public object ConvertBack(object value, Type targetType, object parameter, System.Globalization.CultureInfo culture)
            => throw new NotImplementedException();
    }

    public class NoiseButtonConverter : IValueConverter
    {
        public static readonly NoiseButtonConverter Instance = new();
        public object Convert(object value, Type targetType, object parameter, System.Globalization.CultureInfo culture)
            => value is bool isGenerating && isGenerating ? "ВЫКЛ" : "ВКЛ";
        public object ConvertBack(object value, Type targetType, object parameter, System.Globalization.CultureInfo culture)
            => throw new NotImplementedException();
    }
}
