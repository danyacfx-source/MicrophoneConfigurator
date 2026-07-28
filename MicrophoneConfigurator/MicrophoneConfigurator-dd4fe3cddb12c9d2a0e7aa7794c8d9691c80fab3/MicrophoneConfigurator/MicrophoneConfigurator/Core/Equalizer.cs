using System;
using NAudio.Wave;
using NAudio.Wave.SampleProviders;

namespace MicrophoneConfigurator.Core
{
    public class Equalizer : ISampleProvider
    {
        private readonly ISampleProvider _source;
        private readonly double _sampleRate;
        private readonly BiquadFilter[] _filters;

        private static readonly int[] Frequencies = { 31, 62, 125, 250, 500, 1000, 2000, 4000, 8000, 16000 };
        private const double DefaultBandwidth = 1.0;
        private const double DefaultGain = 0.0;

        public Equalizer(ISampleProvider source, float sampleRate)
        {
            _source = source;
            _sampleRate = sampleRate;
            WaveFormat = source.WaveFormat;

            _filters = new BiquadFilter[10];
            for (int i = 0; i < 10; i++)
            {
                _filters[i] = new BiquadFilter(
                    sampleRate,
                    Frequencies[i],
                    DefaultBandwidth,
                    DefaultGain
                );
            }
        }

        public WaveFormat WaveFormat { get; }

        public void SetBand(int band, float gainDb)
        {
            if (band >= 0 && band < _filters.Length)
            {
                _filters[band].UpdateGain(gainDb);
            }
        }

        public int Read(float[] buffer, int offset, int count)
        {
            int read = _source.Read(buffer, offset, count);

            for (int i = offset; i < offset + read; i++)
            {
                float sample = buffer[i];
                for (int b = 0; b < _filters.Length; b++)
                {
                    sample = _filters[b].Process(sample);
                }
                buffer[i] = sample;
            }

            return read;
        }
    }

    public class BiquadFilter
    {
        private double _a0, _a1, _a2;
        private double _b0, _b1, _b2;
        private double _x1, _x2, _y1, _y2;
        private readonly double _sampleRate;
        private readonly int _frequency;
        private readonly double _bandwidth;
        private double _gainDb;

        public BiquadFilter(double sampleRate, int frequency, double bandwidth, double gainDb)
        {
            _sampleRate = sampleRate;
            _frequency = frequency;
            _bandwidth = bandwidth;
            _gainDb = gainDb;
            RecalculateCoefficients();
        }

        public void UpdateGain(double gainDb)
        {
            _gainDb = gainDb;
            RecalculateCoefficients();
        }

        private void RecalculateCoefficients()
        {
            double A = Math.Pow(10.0, _gainDb / 40.0);
            double w0 = 2.0 * Math.PI * _frequency / _sampleRate;
            double alpha = Math.Sin(w0) * Math.Sinh(Math.Log(2.0) / 2.0 * _bandwidth * w0 / Math.Sin(w0));

            double cosW0 = Math.Cos(w0);
            double sqrtA2alpha = 2.0 * Math.Sqrt(A) * alpha;

            if (Math.Abs(_gainDb) < 0.001)
            {
                _b0 = 1.0; _b1 = 0.0; _b2 = 0.0;
                _a0 = 1.0; _a1 = 0.0; _a2 = 0.0;
            }
            else
            {
                _b0 = A * ((A + 1.0) - (A - 1.0) * cosW0 + sqrtA2alpha);
                _b1 = 2.0 * A * ((A - 1.0) - (A + 1.0) * cosW0);
                _b2 = A * ((A + 1.0) - (A - 1.0) * cosW0 - sqrtA2alpha);
                _a0 = (A + 1.0) + (A - 1.0) * cosW0 + 2.0 * Math.Sqrt(A) * alpha;
                _a1 = -2.0 * ((A - 1.0) + (A + 1.0) * cosW0);
                _a2 = (A + 1.0) + (A - 1.0) * cosW0 - 2.0 * Math.Sqrt(A) * alpha;
            }

            _a1 /= _a0;
            _a2 /= _a0;
            _b0 /= _a0;
            _b1 /= _a0;
            _b2 /= _a0;
        }

        public float Process(float input)
        {
            double output = _b0 * input + _b1 * _x1 + _b2 * _x2 - _a1 * _y1 - _a2 * _y2;

            _x2 = _x1;
            _x1 = input;
            _y2 = _y1;
            _y1 = output;

            return (float)output;
        }
    }
}
