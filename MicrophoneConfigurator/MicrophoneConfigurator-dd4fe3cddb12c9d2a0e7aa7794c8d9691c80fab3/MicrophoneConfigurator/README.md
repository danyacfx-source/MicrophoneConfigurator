# MicStudio Pro

![.NET](https://img.shields.io/badge/.NET-8.0-512BD4?logo=dotnet)
![NAudio](https://img.shields.io/badge/NAudio-2.2.1-orange)
![WPF](https://img.shields.io/badge/WPF-purple)
![License](https://img.shields.io/badge/License-MIT-green)

Профессиональный конфигуратор микрофона для Windows с real-time обработкой звука, голосовым морфингом, пространственным звуком и системой пресетов.

## Возможности

### Основные
- **Выбор устройств** — поддержка любых микрофонов и динамиков (WDM/MME)
- **10-полосный эквалайзер** — параметрический EQ на biquad IIR фильтрах
- **VU-метер** — стерео индикатор уровня с **peak hold** и цветовой индикацией
- **Спектральный анализатор** — real-time визуализация с градиентными барами и пиковыми индикаторами
- **Метрика Gain Reduction** — визуальное отображение работы компрессора/лимитера
- **Запись звука** — сохранение в WAV файл
- **Горячие клавиши** — Space (старт/стоп), Ctrl+R (запись)
- **Система пресетов** — сохранение/загрузка/удаление настроек (JSON в %APPDATA%)

### Dynamics
- **Компрессор** — порог, соотношение, атака, затухание
- **Лимитер** — защита от перегрузки с настраиваемым порогом
- **Шумоподавление (Noise Gate)** — порог, атака, затухание, гистерезис
- **Автоусиление (AGC)** — автоматическая нормализация уровня с настройкой целевого уровня и максимума

### Голос и Эффекты
- **Изменение голоса (Pitch Shifting)** — от 0.5x (низкий) до 2.0x (высокий) с overlap-add алгоритмом
- **Реверберация** — Schroeder алгоритм с 4 comb-фильтрами и 2 allpass-фильтрами
- **Эхо/Делей** — настраиваемая задержка с обратной связью

## Требования

- Windows 10/11
- .NET 8.0 SDK

## Сборка и запуск

```bash
cd MicrophoneConfigurator
dotnet restore
dotnet build
dotnet run
```

## Структура проекта

```
MicrophoneConfigurator/
├── Core/
│   ├── AudioEngine.cs          — Основной движок + цепочка обработки
│   ├── AudioDevice.cs          — Модель устройства
│   ├── AudioPreset.cs          — Модель пресета (все параметры)
│   ├── Equalizer.cs            — 10-полосный EQ (biquad IIR)
│   ├── EqualizerBandModel.cs   — MVVM модель полосы EQ
│   ├── Compressor.cs           — Компрессор
│   ├── Limiter.cs              — Лимитер
│   ├── NoiseGate.cs            — Шумоподавление
│   ├── PitchShifter.cs         — Изменение высоты голоса
│   ├── Reverb.cs               — Реверберация (Schroeder)
│   ├── EchoDelay.cs            — Эхо/Делей
│   ├── AutoGain.cs             — Автоусиление (AGC)
│   └── SpectrumAnalyzer.cs     — FFT анализатор спектра
├── ViewModels/
│   └── MainViewModel.cs        — ViewModel (CommunityToolkit.Mvvm)
├── Resources/
│   └── Styles.xaml             — Современный тёмный UI
├── App.xaml                    — Точка входа
├── MainWindow.xaml             — Главное окно (5 вкладок)
└── MainWindow.xaml.cs          — Code-behind + визуализация
```

## Цепочка обработки звука

```
WaveIn → Volume → AutoGain → Equalizer → PitchShifter → NoiseGate
  → Compressor → Limiter → Reverb → Echo → Recording → Spectrum → WaveOut
```

## Архитектура

- **Паттерн MVVM** с CommunityToolkit.Mvvm (`ObservableObject`, `RelayCommand`, `[ObservableProperty]`)
- **Потокобезопасность**: блокировки на `AudioEngine` и `CircularBuffer`
- **Peak Hold VU-метер** с автоматическим затуханием пиков
- **Biquad IIR фильтры** для эквалайзера (правильная реализация с state variables)
- **Schroeder Reverberator** — классический алгоритм с comb + allpass фильтрами
- **Overlap-Add Pitch Shifter** — оконная функция для плавенного сдвига высоты

## Вкладки

| Вкладка | Описание |
|---------|----------|
| **УСТРОЙСТВА** | Выбор микрофона/динамиков, управление записью |
| **ЭКВАЛАЙЗЕР** | 10-полосный параметрический EQ |
| **ЭФФЕКТЫ** | Компрессор, лимитер, пресеты |
| **ГОЛОС** | Pitch shifting, автоусиление (AGC) |
| **ПРОСТРАНСТВО** | Реверберация, эхо/делей |

## Пресеты

Пресеты сохраняются в:
```
%APPDATA%\MicrophoneConfigurator\Presets\
```
Формат: JSON (все параметры включая новые эффекты)

## Лицензия

MIT
