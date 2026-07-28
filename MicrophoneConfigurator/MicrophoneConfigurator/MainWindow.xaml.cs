using System;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Data;
using System.Windows.Media.Effects;
using System.Windows.Input;
using System.Windows.Media;
using System.Windows.Threading;
using MicrophoneConfigurator.ViewModels;

namespace MicrophoneConfigurator
{
    public partial class MainWindow : Window
    {
        private MainViewModel _viewModel;
        private DispatcherTimer _visualizationTimer;
        private float[] _smoothedSpectrum;
        private float[] _peakHold;
        private float[] _peakDecay;
        private double _vuLeftPeak;
        private double _vuRightPeak;
        private DispatcherTimer _peakDecayTimer;

        public MainWindow()
        {
            InitializeComponent();

            _viewModel = new MainViewModel(App.AudioEngine);
            DataContext = _viewModel;

            _smoothedSpectrum = new float[64];
            _peakHold = new float[64];
            _peakDecay = new float[64];

            _viewModel.AudioDataUpdated += OnAudioDataUpdated;

            _visualizationTimer = new DispatcherTimer { Interval = TimeSpan.FromMilliseconds(30) };
            _visualizationTimer.Tick += (s, e) => RedrawVisualization();
            _visualizationTimer.Start();

            _peakDecayTimer = new DispatcherTimer { Interval = TimeSpan.FromMilliseconds(100) };
            _peakDecayTimer.Tick += (s, e) => DecayPeaks();
            _peakDecayTimer.Start();

            Loaded += (s, e) => _viewModel.RefreshDevicesCommand.Execute(null);
        }

        private void Window_KeyDown(object sender, KeyEventArgs e)
        {
            if (e.Key == Key.Space && Keyboard.Modifiers == ModifierKeys.None)
            {
                if (_viewModel.IsMonitoring)
                    _viewModel.StopMonitoringCommand.Execute(null);
                else
                    _viewModel.StartMonitoringCommand.Execute(null);
                e.Handled = true;
            }
            else if (e.Key == Key.R && Keyboard.Modifiers == ModifierKeys.Control)
            {
                if (_viewModel.IsRecording)
                    _viewModel.StopRecordingCommand.Execute(null);
                else
                    _viewModel.StartRecordingCommand.Execute(null);
                e.Handled = true;
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
        private void CloseBtn_Click(object sender, RoutedEventArgs e) => Close();

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
                _peakHold[i] *= 0.95f;
                if (_peakHold[i] < 0.01f) _peakHold[i] = 0;
            }

            double decayRate = 0.92;
            _vuLeftPeak *= decayRate;
            _vuRightPeak *= decayRate;
            if (_vuLeftPeak < 0.5) VuLeftPeak.Height = 0;
            if (_vuRightPeak < 0.5) VuRightPeak.Height = 0;
        }

        private void UpdateVuMeter(float[] data)
        {
            if (data == null || data.Length == 0) return;

            float level = 0;
            for (int i = 0; i < data.Length; i++)
                level += data[i];
            level /= data.Length;

            double height = Math.Min(level * 350, 130);
            double db = level > 0 ? 20 * Math.Log10(level) : -60;

            VuLeftBar.Height = height;
            VuRightBar.Height = height * 0.95;

            double peakHeight = Math.Max(height, VuLeftPeak.Height);
            VuLeftPeak.Height = peakHeight;
            VuRightPeak.Height = peakHeight * 0.95;

            VuPeakLabel.Text = $"{db:F0} dB";

            if (db > -6)
                VuPeakLabel.Foreground = new SolidColorBrush(Colors.Red);
            else if (db > -18)
                VuPeakLabel.Foreground = new SolidColorBrush(Color.FromRgb(253, 203, 110));
            else
                VuPeakLabel.Foreground = new SolidColorBrush(Color.FromRgb(136, 136, 170));
        }

        private void UpdateGainReduction()
        {
            float gr = _viewModel.GainReduction;
            double normalized = Math.Max(0, Math.Min(1, (-gr) / 30.0));
            double maxWidth = 198;
            GainReductionBar.Width = normalized * maxWidth;
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
                float raw = data[i];
                float target = raw * 3.5f;
                target = Math.Min(target, 1.0f);

                _smoothedSpectrum[i] += (target - _smoothedSpectrum[i]) * 0.35f;

                if (_smoothedSpectrum[i] > _peakHold[i])
                {
                    _peakHold[i] = _smoothedSpectrum[i];
                }

                double height = _smoothedSpectrum[i] * canvasHeight;
                height = Math.Max(height, 2);

                double peakHeight = _peakHold[i] * canvasHeight;
                peakHeight = Math.Max(peakHeight, 2);

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
                };

                bar.Fill = new LinearGradientBrush(
                    barColor,
                    Color.FromArgb(30, barColor.R, barColor.G, barColor.B),
                    90);

                bar.Effect = new DropShadowEffect
                {
                    Color = barColor,
                    BlurRadius = 10,
                    ShadowDepth = 0,
                    Opacity = 0.35
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
        {
            if (value is float vol)
                return $"{(vol * 100):F0}%";
            return "100%";
        }

        public object ConvertBack(object value, Type targetType, object parameter, System.Globalization.CultureInfo culture)
        {
            throw new NotImplementedException();
        }
    }
}
