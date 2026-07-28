using System;
using NAudio.Wave;

namespace MicrophoneConfigurator.Core
{
    public class NoiseGateSampleProvider : ISampleProvider
    {
        private readonly ISampleProvider _source;
        private float _envelopeUp;
        private float _envelopeDown;
        private float _gain;
        private bool _isOpen;

        public float Threshold { get; set; } = 0.05f;
        public float Attack { get; set; } = 0.005f;
        public float Release { get; set; } = 0.1f;
        public bool Enabled { get; set; } = true;
        public float Hysteresis { get; set; } = 0.7f;
        public float SpectralSmoothing { get; set; } = 0.92f;

        public NoiseGateSampleProvider(ISampleProvider source)
        {
            _source = source;
            WaveFormat = source.WaveFormat;
        }

        public WaveFormat WaveFormat { get; }

        public int Read(float[] buffer, int offset, int count)
        {
            int read = _source.Read(buffer, offset, count);

            if (!Enabled)
                return read;

            float attackCoeff = (float)Math.Exp(-1.0 / (WaveFormat.SampleRate * Math.Max(Attack, 0.0001f)));
            float releaseCoeff = (float)Math.Exp(-1.0 / (WaveFormat.SampleRate * Math.Max(Release, 0.001f)));
            float openThreshold = Threshold;
            float closeThreshold = Threshold * Hysteresis;

            for (int i = offset; i < offset + read; i++)
            {
                float sample = buffer[i];
                float absSample = Math.Abs(sample);

                float upCoeff = absSample > _envelopeUp ? attackCoeff : releaseCoeff;
                _envelopeUp = upCoeff * _envelopeUp + (1.0f - upCoeff) * absSample;

                float downCoeff = absSample > _envelopeDown ? 0.001f : releaseCoeff;
                _envelopeDown = downCoeff * _envelopeDown + (1.0f - downCoeff) * absSample;

                if (!_isOpen && _envelopeUp > openThreshold)
                    _isOpen = true;
                else if (_isOpen && _envelopeDown < closeThreshold)
                    _isOpen = false;

                float targetGain = _isOpen ? 1.0f : 0.0f;
                float gainSpeed = _isOpen ? attackCoeff : releaseCoeff;
                _gain = gainSpeed * _gain + (1.0f - gainSpeed) * targetGain;

                float cosFactor = (float)Math.Cos((_gain - 0.5f) * Math.PI);
                float smoothGain = (1.0f - cosFactor) * 0.5f;

                buffer[i] *= smoothGain;
            }

            return read;
        }
    }
}
