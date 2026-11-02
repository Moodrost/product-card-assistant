---
name: "Карточка"
description: "Спокойный рабочий редактор исходного JSON и черновика карточки товара."
colors:
  background: "#f5f5f0"
  surface: "#fff"
  input-panel: "#fcfcf8"
  input: "#f3f5ef"
  text: "#253a34"
  primary: "#173f35"
  primary-hover: "#285e4e"
  accent: "#c5df98"
  muted: "#5c6c63"
  line: "#dce1d8"
  selected: "#e7eddf"
  subtle-hover: "#edf0e4"
  focus: "#619749"
  missing: "#895a1c"
  error: "#8f271c"
  error-background: "#fff0ea"
typography:
  headline:
    fontFamily: '"Golos Text", sans-serif'
    fontSize: "clamp(27px, 3vw, 39px)"
    fontWeight: 550
    lineHeight: 1.2
    letterSpacing: "-0.035em"
  title:
    fontFamily: '"Golos Text", sans-serif'
    fontSize: "17px"
    fontWeight: 550
    letterSpacing: "-0.02em"
  product-title:
    fontFamily: '"Golos Text", sans-serif'
    fontSize: "20px"
    fontWeight: 500
    lineHeight: 1.5
  lead:
    fontFamily: '"Golos Text", sans-serif'
    fontSize: "14px"
    fontWeight: 400
    lineHeight: 1.65
  body:
    fontFamily: '"Golos Text", sans-serif'
    fontSize: "13px"
    fontWeight: 400
    lineHeight: 1.85
  label:
    fontFamily: '"Golos Text", sans-serif'
    fontSize: "11px"
    fontWeight: 400
  code:
    fontFamily: 'Consolas, "Courier New", monospace'
    fontSize: "12px"
    fontWeight: 400
    lineHeight: 1.8
rounded:
  tab: "4px"
  chip: "5px"
  control: "6px"
  button: "7px"
  field: "8px"
  workspace: "14px"
  badge: "30px"
spacing:
  compact: "8px"
  small: "12px"
  medium: "16px"
  mobile-inline: "18px"
  section: "22px"
  panel: "28px"
  output-inline: "30px"
components:
  button-primary:
    backgroundColor: "{colors.primary}"
    textColor: "{colors.surface}"
    rounded: "{rounded.button}"
    padding: "12px 16px"
    width: "100%"
  button-primary-hover:
    backgroundColor: "{colors.primary-hover}"
  button-copy:
    textColor: "{colors.primary}"
    rounded: "{rounded.control}"
    padding: "9px 11px"
  button-copy-hover:
    backgroundColor: "{colors.subtle-hover}"
  json-input:
    backgroundColor: "{colors.input}"
    typography: "{typography.code}"
    rounded: "{rounded.field}"
    padding: "16px"
    width: "100%"
  workspace:
    backgroundColor: "{colors.surface}"
    rounded: "{rounded.workspace}"
  view-selected:
    backgroundColor: "{colors.selected}"
    textColor: "{colors.primary}"
    rounded: "{rounded.tab}"
    padding: "7px 10px"
---

# Рабочий редактор

## Overview

Сдержанный редактор помогает сверять исходные параметры и готовый текст.
Слева находится JSON, справа — черновик. Светлые поверхности, тонкие границы
и тёмно-зелёные действия поддерживают чтение длинного результата.
Документ фиксирует существующий интерфейс; значения frontmatter нормативны.

## Colors

Основной зелёный объединяет заголовок, логотип и действие подготовки карточки.
Светлый акцент используется в знаке и выделении текста; выбранный формат
имеет отдельную мягкую заливку. Нейтральные оттенки различают фон страницы,
панель ввода и поле JSON. Вторичный текст сохраняет спокойную иерархию.
Ошибки и отсутствующие значения имеют собственные цвета и явную подпись.

## Typography

Golos Text используется во всём интерфейсе, Consolas с резервными шрифтами —
для ввода JSON. Крупный заголовок страницы отделён от названия товара и
заголовков панелей. Описание набрано свободно по высоте строки и ограничено
по ширине (72ch); подписи и вспомогательные действия компактнее.

## Layout

Основной контейнер ограничен по ширине (1540px), внешние боковые отступы
зависят от окна (4vw). Рабочая область состоит из двух колонок
(`minmax(320px, 0.95fr) minmax(0, 1.35fr)`): результат получает больше места.
Панели разделены границей; контент начинается у их верхнего края.

При ширине до 840px панели идут одна за другой, подпись рядом с логотипом
скрывается. До 480px внутренние отступы панелей сокращаются (21px 18px),
заголовок страницы получает фиксированный размер (28px), JSON — меньший
кегль (11px). Кнопки форматов, копирование и поисковые запросы переносятся
по доступной ширине. Длинные значения в результате могут разрываться.

## Elevation & Depth

Рабочие поверхности обходятся без теней. Глубину задают светлые заливки,
границы и отступы; уведомления отделяются тональным фоном.

## Shapes

Рабочая область имеет наиболее заметное скругление, поля и уведомления —
умеренное. Кнопки, переключатели и метки компактнее. Только индикатор
режима выполнен в форме капсулы. Разделители тонкие, без декоративных рамок.

## Components

- Основное действие занимает ширину панели. Его заливка меняется при наведении;
  недоступная кнопка остаётся на месте с уменьшенной непрозрачностью (0.55).
- Поле JSON допускает изменение высоты и сохраняет моноширинный набор.
- Переключатель представления объединён общей рамкой; выбранная кнопка
  отличается заливкой. Копирование оформлено отдельной контурной кнопкой.
- Характеристики образуют простую таблицу с горизонтальными разделителями;
  поисковые запросы показаны переносимыми метками.
- Режим demo/live, ошибки, устаревший результат и необходимость проверки
  выражены текстом. Цвет дополняет сообщение.
- Клавиатурный фокус обозначается зелёной обводкой (3px) с отступом (4px).
  Единственный переход — смена фона кнопки; системная настройка уменьшения
  движения отключает длительность переходов и анимаций.

## Do's and Don'ts

- Сохраняйте порядок «исходные данные → черновик» и возможность сверить значения.
- Используйте существующую иерархию текста, заливок и границ для новых состояний.
- Оставляйте режим и важные ограничения читаемыми без различения цветов.
- Не добавляйте декоративные изображения и тени к рабочим поверхностям.
- Не превращайте технические значения в интерпретируемый HTML.
