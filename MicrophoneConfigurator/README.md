# MicStudio Pro

![.NET](https://img.shields.io/badge/.NET-8.0-512BD4?logo=dotnet)
![NAudio](https://img.shields.io/badge/NAudio-2.2.1-orange)
![WPF](https://img.shields.io/badge/WPF-purple)
![License](https://img.shields.io/badge/License-MIT-green)

Профессиональный конфигуратор микрофона для Windows с real-time обработкой звука, визуализацией спектра и системой пресетов.

## Возможности

- **Выбор устройств** — поддержка любых микрофонов и динамиков (WDM/MME)
- **10-полосный эквалайзер** — параметрический EQ с правильной biquad IIR фильтрацией
- **Компрессор** — порог, соотношение, атака, затухание
- **Лимитер** — защита от перегрузки с настраиваемым порогом
- **Шумоподавление (Noise Gate)** — порог, атака, затухание, гистерезис
- **Визуализация** — real-time спектральный анализатор с градиентной отрисовкой
- **VU-метер** — стерео индикатор уровня (L/R)
- **Метрика Gain Reduction** — визуальное отображение работы компрессора/лимитера
- **Запись звука** — сохранение в WAV файл
- **Система пресетов** — сохранение/загрузка/удаление настроек (JSON в %APPDATA%)
- **Горячие клавиши** — Space (старт/стоп), Ctrl+R (запись)

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
│   ├── AudioEngine.cs          — Основной движок аудио + запись
│   ├── AudioDevice.cs          — Модель устройства
│   ├── AudioPreset.cs          — Модель пресета
│   ├── Equalizer.cs            — 10-полосный EQ (biquad IIR фильтры)
│   ├── EqualizerBandModel.cs   — MVVM модель полосы EQ
│   ├── Compressor.cs           — Компрессор
│   ├── Limiter.cs              — Лимитер
│   ├── NoiseGate.cs            — Шумоподавление
│   └── SpectrumAnalyzer.cs     — FFT анализатор спектра
├── ViewModels/
│   └── MainViewModel.cs        — ViewModel (CommunityToolkit.Mvvm)
├── Resources/
│   └── Styles.xaml             — Современный тёмный UI
├── App.xaml                    — Точка входа
├── MainWindow.xaml             — Главное окно
└── MainWindow.xaml.cs          — Code-behind + визуализация
```

## Архитектура

- **Паттерн MVVM** с CommunityToolkit.Mvvm (`ObservableObject`, `RelayCommand`, `[ObservableProperty]`)
- **Цепочка обработки**: `WaveIn → Volume → Equalizer → NoiseGate → Compressor → Limiter → Recording → Spectrum → WaveOut`
- **Потокобезопасность**: блокировки на `AudioEngine` и `CircularBuffer`
- **Biquad IIR фильтры** для эквалайзера (правильная реализация с state variables)

## Пресеты

Пресеты сохраняются в:
```
%APPDATA%\MicrophoneConfigurator\Presets\
```
Формат: JSON

## Использование

1. Запустите приложение
2. Выберите микрофон на вкладке "Устройства"
3. Нажмите "СЛУШАТЬ" для мониторинга (или нажмите Space)
4. Настройте эквалайзер, компрессор, лимитер, шумоподавление
5. Сохраните пресет для повторного использования
6. Используйте запись для сохранения аудио в WAV

## Лицензия

MIT
