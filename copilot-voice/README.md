# Copilot Voice Input 🎤

VS Code расширение для голосового ввода в GitHub Copilot Chat через Groq Whisper API.

## Возможности

- Горячая клавиша `Ctrl+Shift+M` (`Cmd+Shift+M` на macOS) — запуск/остановка записи
- Распознанный текст вставляется в поле Copilot Chat — можно отредактировать перед отправкой
- Иконка в статус-баре отображает текущее состояние: `idle` / `recording` / `processing`
- Поддержка Windows, macOS, Linux

## Требования

### Groq API ключ

1. Зарегистрируйтесь на `https://console.groq.com`
2. Создайте API ключ
3. Укажите его в настройках VS Code: `copilotVoice.groqApiKey`

### Утилита записи звука

- macOS / Linux: установите SoX

```bash
# macOS
brew install sox

# Ubuntu / Debian
sudo apt install sox
```

- Windows: установите FFmpeg и добавьте в `PATH`

## Настройки

| Настройка | Тип | По умолчанию | Описание |
|---|---|---|---|
| `copilotVoice.groqApiKey` | `string` | `""` | API ключ Groq |
| `copilotVoice.language` | `string` | `"ru"` | Язык распознавания (`ru`, `en`, ...) |

## Использование

1. Нажмите `Ctrl+Shift+M` или кликните на 🎤 в статус-баре
2. Говорите в микрофон
3. Нажмите `Ctrl+Shift+M` снова для остановки
4. Текст появится в поле ввода Copilot Chat
5. Отредактируйте при необходимости и отправьте

## Сборка из исходников

```bash
cd copilot-voice
npm install
npm run compile
```

Затем нажмите `F5` в VS Code для запуска в режиме отладки.
