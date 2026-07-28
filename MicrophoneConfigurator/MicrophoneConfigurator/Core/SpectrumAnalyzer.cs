using System;
using System.Numerics;
using NAudio.Wave;

namespace MicrophoneConfigurator.Core
{
    public class SpectrumAnalyzerSampleProvider : ISampleProvider
    {
        private readonly ISampleProvider _source;
        private readonly float[] _fftBuffer;
        private readonly float[] _window;
        private readonly float[] _spectrumData;
        private readonly float[] _waveformData;
        private int _fftPos;
        private const int FftSize = 512;

        public event Action<float[], float[]>? SpectrumCalculated;

        public SpectrumAnalyzerSampleProvider(ISampleProvider source)
        {
            _source = source;
            WaveFormat = source.WaveFormat;
            _fftBuffer = new float[FftSize];
            _spectrumData = new float[64];
            _waveformData = new float[256];

            _window = new float[FftSize];
            for (int i = 0; i < FftSize; i++)
                _window[i] = 0.5f * (1.0f - (float)Math.Cos(2.0 * Math.PI * i / (FftSize - 1)));
        }

        public WaveFormat WaveFormat { get; }

        public int Read(float[] buffer, int offset, int count)
        {
            int read = _source.Read(buffer, offset, count);

            for (int i = 0; i < read; i++)
            {
                _fftBuffer[_fftPos] = buffer[offset + i];
                _fftPos++;

                if (_fftPos >= FftSize)
                {
                    _fftPos = 0;
                    ProcessFFT();
                }

                int waveformIndex = (int)((float)i / read * _waveformData.Length);
                if (waveformIndex < _waveformData.Length)
                    _waveformData[waveformIndex] = buffer[offset + i];
            }

            return read;
        }

        private void ProcessFFT()
        {
            var fftComplex = new Complex[FftSize];
            for (int i = 0; i < FftSize; i++)
                fftComplex[i] = new Complex(_fftBuffer[i] * _window[i], 0);

            FFT(fftComplex);

            int usableBins = FftSize / 2;
            for (int i = 0; i < _spectrumData.Length; i++)
            {
                float freqRatio = (float)i / _spectrumData.Length;
                int index = (int)(freqRatio * freqRatio * usableBins * 0.8f);
                index = Math.Min(index, usableBins - 1);

                float magnitude = (float)Math.Sqrt(
                    fftComplex[index].Real * fftComplex[index].Real +
                    fftComplex[index].Imaginary * fftComplex[index].Imaginary
                );

                float normalized = magnitude / (FftSize * 0.5f);
                _spectrumData[i] = Math.Min(normalized * 2.0f, 1.0f);
            }

            SpectrumCalculated?.Invoke(_spectrumData, _waveformData);
        }

        private static void FFT(Complex[] data)
        {
            int n = data.Length;
            if (n == 0) return;

            int bits = (int)Math.Log2(n);
            var result = new Complex[n];

            for (int i = 0; i < n; i++)
            {
                int reversed = ReverseBits(i, bits);
                result[reversed] = data[i];
            }

            for (int size = 2; size <= n; size *= 2)
            {
                int halfSize = size / 2;
                double angle = -2 * Math.PI / size;
                var wn = new Complex(Math.Cos(angle), Math.Sin(angle));

                for (int i = 0; i < n; i += size)
                {
                    var w = new Complex(1, 0);
                    for (int j = 0; j < halfSize; j++)
                    {
                        var u = result[i + j];
                        var v = Complex.Multiply(result[i + j + halfSize], w);
                        result[i + j] = u + v;
                        result[i + j + halfSize] = u - v;
                        w = Complex.Multiply(w, wn);
                    }
                }
            }

            Array.Copy(result, data, n);
        }

        private static int ReverseBits(int value, int bits)
        {
            int result = 0;
            for (int i = 0; i < bits; i++)
            {
                result = (result << 1) | (value & 1);
                value >>= 1;
            }
            return result;
        }
    }
}
