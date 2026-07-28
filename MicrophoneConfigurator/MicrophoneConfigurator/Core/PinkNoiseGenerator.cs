using System;
using NAudio.Wave;

namespace MicrophoneConfigurator.Core
{
    public class PinkNoiseGenerator : ISampleProvider
    {
        private float _b0 = 0, _b1 = 0, _b2 = 0, _b3 = 0, _b4 = 0, _b5 = 0, _b6 = 0;
        private readonly Random _random = new();
        public bool IsGenerating { get; set; }

        public WaveFormat WaveFormat { get; } = new WaveFormat(44100, 32, 1);

        public int Read(float[] buffer, int offset, int count)
        {
            if (!IsGenerating)
            {
                for (int i = offset; i < offset + count; i++)
                    buffer[i] = 0;
                return count;
            }

            for (int i = offset; i < offset + count; i++)
            {
                float white = (float)(_random.NextDouble() * 2.0 - 1.0);

                _b0 = 0.99886f * _b0 + white * 0.0555179f;
                _b1 = 0.99332f * _b1 + white * 0.0750759f;
                _b2 = 0.96900f * _b2 + white * 0.1538520f;
                _b3 = 0.86650f * _b3 + white * 0.3104856f;
                _b4 = 0.55000f * _b4 + white * 0.5329522f;
                _b5 = -0.7616f * _b5 - white * 0.0168980f;

                buffer[i] = (_b0 + _b1 + _b2 + _b3 + _b4 + _b5 + _b6 + white * 0.5362f) * 0.11f;
                _b6 = white * 0.115926f;
            }

            return count;
        }
    }
}
