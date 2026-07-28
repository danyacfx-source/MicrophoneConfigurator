using System;
using NAudio.Wave;

namespace MicrophoneConfigurator.Core
{
    public class EchoDelaySampleProvider : ISampleProvider
    {
        private readonly ISampleProvider _source;
        private readonly float[] _delayBuffer;
        private int _writePos;
        private int _readPos;

        public float DelayMs { get; set; } = 200f;
        public float Feedback { get; set; } = 0.4f;
        public float WetMix { get; set; } = 0.3f;
        public bool Enabled { get; set; } = false;

        public EchoDelaySampleProvider(ISampleProvider source)
        {
            _source = source;
            WaveFormat = source.WaveFormat;
            int maxDelaySamples = (int)(WaveFormat.SampleRate * 2.0f);
            _delayBuffer = new float[Math.Max(maxDelaySamples, 1)];
        }

        public WaveFormat WaveFormat { get; }

        private int DelaySamples => Math.Max(1, (int)(WaveFormat.SampleRate * DelayMs / 1000f));

        public int Read(float[] buffer, int offset, int count)
        {
            int read = _source.Read(buffer, offset, count);

            if (!Enabled)
                return read;

            int delayLen = _delayBuffer.Length;

            for (int i = offset; i < offset + read; i++)
            {
                _delayBuffer[_writePos] = buffer[i] + _delayBuffer[_readPos] * Feedback;
                _writePos = (_writePos + 1) % delayLen;

                buffer[i] = buffer[i] * (1.0f - WetMix) + _delayBuffer[_readPos] * WetMix;

                _readPos = (_readPos + 1) % delayLen;
            }

            int delaySamps = DelaySamples;
            _readPos = (_writePos - delaySamps + delayLen) % delayLen;

            return read;
        }
    }
}
