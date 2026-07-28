using System;
using NAudio.Wave;

namespace MicrophoneConfigurator.Core
{
    public class LimiterSampleProvider : ISampleProvider
    {
        private readonly ISampleProvider _source;
        private float _envelope;

        public float Threshold { get; set; } = 0.9f;
        public float Release { get; set; } = 0.05f;

        public LimiterSampleProvider(ISampleProvider source)
        {
            _source = source;
            WaveFormat = source.WaveFormat;
        }

        public WaveFormat WaveFormat { get; }

        public int Read(float[] buffer, int offset, int count)
        {
            int read = _source.Read(buffer, offset, count);

            float releaseCoeff = (float)Math.Exp(-1.0 / (WaveFormat.SampleRate * Release));

            for (int i = offset; i < offset + read; i++)
            {
                float input = Math.Abs(buffer[i]);

                float coeff = input > _envelope ? 0.0f : releaseCoeff;
                _envelope = coeff * _envelope + (1.0f - coeff) * input;

                if (_envelope > Threshold)
                {
                    float gain = Threshold / _envelope;
                    buffer[i] *= gain;
                }
            }

            return read;
        }
    }
}
