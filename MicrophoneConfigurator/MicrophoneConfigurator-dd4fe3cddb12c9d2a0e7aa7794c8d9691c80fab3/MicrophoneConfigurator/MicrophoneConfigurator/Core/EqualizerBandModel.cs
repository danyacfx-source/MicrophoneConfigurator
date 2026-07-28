using CommunityToolkit.Mvvm.ComponentModel;
using CommunityToolkit.Mvvm.Input;

namespace MicrophoneConfigurator.Core
{
    public partial class EqualizerBandModel : ObservableObject
    {
        [ObservableProperty]
        private string _label = string.Empty;

        [ObservableProperty]
        private float _value;

        [ObservableProperty]
        private int _index;

        public float MinValue { get; set; } = -12f;
        public float MaxValue { get; set; } = 12f;
    }
}
