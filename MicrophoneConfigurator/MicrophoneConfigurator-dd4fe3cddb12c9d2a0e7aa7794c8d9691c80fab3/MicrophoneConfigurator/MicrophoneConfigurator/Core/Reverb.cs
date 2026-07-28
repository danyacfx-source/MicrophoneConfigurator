using System;
using NAudio.Wave;

namespace MicrophoneConfigurator.Core
{
    public class ReverbSampleProvider : ISampleProvider
    {
        private readonly ISampleProvider _source;
        private readonly float[] _comb1Buffer;
        private readonly float[] _comb2Buffer;
        private readonly float[] _comb3Buffer;
        private readonly float[] _comb4Buffer;
        private readonly float[] _allpass1Buffer;
        private readonly float[] _allpass2Buffer;
        private int _comb1Pos, _comb2Pos, _comb3Pos, _comb4Pos;
        private int _allpass1Pos, _allpass2Pos;
        private float _comb1Out, _comb2Out, _comb3Out, _comb4Out;
        private float _allpass1Out, _allpass2Out;

        public float WetMix { get; set; } = 0.3f;
        public float RoomSize { get; set; } = 0.7f;
        public float Damping { get; set; } = 0.5f;
        public bool Enabled { get; set; } = false;

        public ReverbSampleProvider(ISampleProvider source)
        {
            _source = source;
            WaveFormat = source.WaveFormat;
            int sr = WaveFormat.SampleRate;

            int combSize1 = (int)(sr * 0.0297f);
            int combSize2 = (int)(sr * 0.0371f);
            int combSize3 = (int)(sr * 0.0411f);
            int combSize4 = (int)(sr * 0.0437f);
            int allpassSize1 = (int)(sr * 0.0053f);
            int allpassSize2 = (int)(sr * 0.0127f);

            _comb1Buffer = new float[Math.Max(combSize1, 1)];
            _comb2Buffer = new float[Math.Max(combSize2, 1)];
            _comb3Buffer = new float[Math.Max(combSize3, 1)];
            _comb4Buffer = new float[Math.Max(combSize4, 1)];
            _allpass1Buffer = new float[Math.Max(allpassSize1, 1)];
            _allpass2Buffer = new float[Math.Max(allpassSize2, 1)];
        }

        public WaveFormat WaveFormat { get; }

        public int Read(float[] buffer, int offset, int count)
        {
            int read = _source.Read(buffer, offset, count);

            if (!Enabled)
                return read;

            float feedback = RoomSize;
            float damp = Damping;

            for (int i = offset; i < offset + read; i++)
            {
                float input = buffer[i];
                float combSum = 0;

                _comb1Buffer[_comb1Pos] = input + _comb1Out * feedback * (1.0f - damp) + _comb1Buffer[_comb1Pos] * damp;
                _comb1Out = _comb1Buffer[_comb1Pos];
                _comb1Pos = (_comb1Pos + 1) % _comb1Buffer.Length;
                combSum += _comb1Out;

                _comb2Buffer[_comb2Pos] = input + _comb2Out * feedback * (1.0f - damp) + _comb2Buffer[_comb2Pos] * damp;
                _comb2Out = _comb2Buffer[_comb2Pos];
                _comb2Pos = (_comb2Pos + 1) % _comb2Buffer.Length;
                combSum += _comb2Out;

                _comb3Buffer[_comb3Pos] = input + _comb3Out * feedback * (1.0f - damp) + _comb3Buffer[_comb3Pos] * damp;
                _comb3Out = _comb3Buffer[_comb3Pos];
                _comb3Pos = (_comb3Pos + 1) % _comb3Buffer.Length;
                combSum += _comb3Out;

                _comb4Buffer[_comb4Pos] = input + _comb4Out * feedback * (1.0f - damp) + _comb4Buffer[_comb4Pos] * damp;
                _comb4Out = _comb4Buffer[_comb4Pos];
                _comb4Pos = (_comb4Pos + 1) % _comb4Buffer.Length;
                combSum += _comb4Out;

                combSum *= 0.25f;

                float apInput = combSum;
                float ap1 = _allpass1Buffer[_allpass1Pos];
                _allpass1Buffer[_allpass1Pos] = apInput + ap1 * 0.5f;
                _allpass1Out = -_allpass1Buffer[_allpass1Pos] + apInput + ap1;
                _allpass1Pos = (_allpass1Pos + 1) % _allpass1Buffer.Length;

                float ap2 = _allpass2Buffer[_allpass2Pos];
                _allpass2Buffer[_allpass2Pos] = _allpass1Out + ap2 * 0.5f;
                _allpass2Out = -_allpass2Buffer[_allpass2Pos] + _allpass1Out + ap2;
                _allpass2Pos = (_allpass2Pos + 1) % _allpass2Buffer.Length;

                buffer[i] = input * (1.0f - WetMix) + _allpass2Out * WetMix;
            }

            return read;
        }
    }
}
