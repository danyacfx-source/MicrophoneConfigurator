using System;
using NAudio.Wave;

namespace MicrophoneConfigurator.Core
{
    public class CompressorSampleProvider : ISampleProvider
    {
        private readonly ISampleProvider _source;
        private float _envelope;

        public float Threshold { get; set; } = 0.5f;
        public float Ratio { get; set; } = 4.0f;
        public float Attack { get; set; } = 0.01f;
        public float Release { get; set; } = 0.1f;

        public CompressorSampleProvider(ISampleProvider source)
        {
            _source = source;
            WaveFormat = source.WaveFormat;
        }

        public WaveFormat WaveFormat { get; }

        public int Read(float[] buffer, int offset, int count)
        {
            int read = _source.Read(buffer, offset, count);

            float attackCoeff = (float)Math.Exp(-1.0 / (WaveFormat.SampleRate * Attack));
            float releaseCoeff = (float)Math.Exp(-1.0 / (WaveFormat.SampleRate * Release));

            for (int i = offset; i < offset + read; i++)
            {
                float input = Math.Abs(buffer[i]);

                float coeff = input > _envelope ? attackCoeff : releaseCoeff;
                _envelope = coeff * _envelope + (1.0f - coeff) * input;

                if (_envelope > Threshold)
                {
                    float gain = Threshold + (1.0f / Ratio) * (_envelope - Threshold);
                    gain /= _envelope;
                    buffer[i] *= gain;
                }
            }

            return read;
        }
    }
}
