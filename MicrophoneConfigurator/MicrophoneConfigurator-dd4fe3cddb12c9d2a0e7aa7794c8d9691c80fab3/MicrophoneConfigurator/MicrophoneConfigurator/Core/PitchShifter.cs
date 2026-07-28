using System;
using NAudio.Wave;

namespace MicrophoneConfigurator.Core
{
    public class PitchShifterSampleProvider : ISampleProvider
    {
        private readonly ISampleProvider _source;
        private readonly float[] _inputBuffer;
        private readonly float[] _outputBuffer;
        private readonly float[] _overlapBuffer;
        private int _inputPos;
        private int _outputPos;
        private int _inputSamplesAvailable;
        private readonly int _frameSize;
        private bool _outputActive;
        private int _outputAvailable;

        public float PitchRatio { get; set; } = 1.0f;
        public bool Enabled { get; set; } = false;

        public PitchShifterSampleProvider(ISampleProvider source)
        {
            _source = source;
            WaveFormat = source.WaveFormat;
            _frameSize = 2048;
            _inputBuffer = new float[_frameSize * 4];
            _outputBuffer = new float[_frameSize * 2];
            _overlapBuffer = new float[_frameSize];
        }

        public WaveFormat WaveFormat { get; }

        public int Read(float[] buffer, int offset, int count)
        {
            if (!Enabled || Math.Abs(PitchRatio - 1.0f) < 0.01f)
            {
                return _source.Read(buffer, offset, count);
            }

            int written = 0;

            while (written < count)
            {
                if (_outputActive && _outputAvailable > 0)
                {
                    int canCopy = Math.Min(_outputAvailable, count - written);
                    Array.Copy(_outputBuffer, _outputPos, buffer, offset + written, canCopy);
                    written += canCopy;
                    _outputPos += canCopy;
                    _outputAvailable -= canCopy;
                }
                else
                {
                    _outputActive = false;
                    ProcessNextFrame();
                }
            }

            return written;
        }

        private void ProcessNextFrame()
        {
            int samplesNeeded = (int)(_frameSize * PitchRatio) + _frameSize;
            int totalAvailable = _inputSamplesAvailable;

            if (totalAvailable < samplesNeeded)
            {
                int space = _inputBuffer.Length - _inputPos;
                if (space < samplesNeeded - totalAvailable)
                {
                    Array.Copy(_inputBuffer, 0, _inputBuffer, _inputPos, totalAvailable);
                    _inputPos = totalAvailable;
                }

                int toRead = Math.Min(samplesNeeded - totalAvailable, _inputBuffer.Length - _inputPos - totalAvailable);
                if (toRead > 0)
                {
                    int read = _source.Read(_inputBuffer, _inputPos + totalAvailable, toRead);
                    _inputSamplesAvailable = totalAvailable + read;
                    if (_inputPos + _inputSamplesAvailable >= _inputBuffer.Length)
                    {
                        _inputPos = 0;
                    }
                }
            }

            if (_inputSamplesAvailable < _frameSize)
            {
                Array.Copy(_inputBuffer, 0, _inputBuffer, _inputPos, _inputSamplesAvailable);
                _inputPos = 0;
                int read = _source.Read(_inputBuffer, _inputSamplesAvailable, _frameSize - _inputSamplesAvailable);
                _inputSamplesAvailable += read;
                if (_inputSamplesAvailable < _frameSize)
                {
                    return;
                }
            }

            int readFrames = (int)(_frameSize * PitchRatio);
            if (readFrames > _inputSamplesAvailable)
                readFrames = _inputSamplesAvailable;
            if (readFrames < 1)
                readFrames = 1;

            for (int i = 0; i < _frameSize; i++)
            {
                float sourcePos = i * PitchRatio;
                int idx = (int)sourcePos;
                float frac = sourcePos - idx;
                int srcIdx = _inputPos + idx;

                if (srcIdx + 1 < _inputBuffer.Length && idx + 1 < _inputSamplesAvailable)
                {
                    float s0 = _inputBuffer[srcIdx];
                    float s1 = _inputBuffer[srcIdx + 1];
                    _outputBuffer[i] = s0 + (s1 - s0) * frac;
                }
                else if (srcIdx < _inputBuffer.Length && idx < _inputSamplesAvailable)
                {
                    _outputBuffer[i] = _inputBuffer[srcIdx];
                }
            }

            for (int i = 0; i < _frameSize && i < _overlapBuffer.Length; i++)
            {
                float window = 0.5f - 0.5f * (float)Math.Cos(2.0 * Math.PI * i / _frameSize);
                _outputBuffer[i] = _outputBuffer[i] * window + _overlapBuffer[i] * (1.0f - window);
                _overlapBuffer[i] = _outputBuffer[i] * window;
            }

            _inputPos += readFrames;
            _inputSamplesAvailable -= readFrames;
            if (_inputPos + _inputSamplesAvailable >= _inputBuffer.Length)
            {
                Array.Copy(_inputBuffer, _inputPos, _inputBuffer, 0, _inputSamplesAvailable);
                _inputPos = 0;
            }

            _outputPos = 0;
            _outputAvailable = _frameSize;
            _outputActive = true;
        }
    }
}
