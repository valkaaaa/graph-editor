# GraphEditor Pro — полный список типов графиков

Версия: 1.5.0. Внутренние ID совпадают с `INTERNAL_TYPES`
в `grapheditor/translator.py` и ключами в `TYPE_TO_KEY`.

## Обозначения
- **Proj** — projection для matplotlib: `2d`, `polar`, `3d`
- **Fields** — какие поля формы используются:
  - `x` — X-данные (или подписи в спец. типах)
  - `y` — Y-данные (или группы через `;`)
  - `z` — Z-данные (или матрица через `;`, или формула)
  - `yerr` — погрешности / V-компонента
  - `pie` — подписи (через запятую)
  - `colors` — HEX-цвета (через запятую)
  - `matrix` — матрица `Z` через `;`
  - `box` — группы `Y` через `;`
- **HTML** — есть ли экспорт в интерактивный HTML через Plotly
  - `full` — есть, полный
  - `partial` — есть, упрощённый
  - `—` — нет (только matplotlib)

---

## 2D · Базовые

| ID                         | EN          | RU          | Proj | Fields                 | HTML |
|----------------------------|-------------|-------------|------|------------------------|------|
| `Линия`                    | Line        | Линия       | 2d   | x, y, yerr, fill       | full |
| `Столбчатая`               | Bar         | Столбчатая  | 2d   | x, y, yerr             | full |
| `Гистограмма`              | Histogram   | Гистограмма | 2d   | x, bins                | full |
| `Точечная`                 | Scatter     | Точечная    | 2d   | x, y, yerr, glow       | full |
| `Круговая`                 | Pie         | Круговая    | 2d   | y, pie, colors         | full |
| `Step plot`                | Step        | Шаговая     | 2d   | x, y                   | full |
| `Полигон`                  | Polygon     | Полигон     | 2d   | x, y                   | full |
| `Столбчатая с накоплением` | Stacked bar | Накопленная | 2d   | x, y (groups)          | full |
| `Пузырьковая`              | Bubble      | Пузырьковая | 2d   | x, y, z (размер)       | full |
| `Кольцевая`                | Donut       | Кольцевая   | 2d   | y, pie, colors         | full |
| `Вложенная круговая`       | Nested pie  | Вложенная   | 2d   | y (rings), pie, colors | —    |
| `Мозаика`                  | Mosaic      | Мозаика     | 2d   | y (matrix), pie        | —    |

## 2D · Статистические

| ID                      |           EN           | RU                 | Proj | Fields                   | HTML |
|-------------------------|:----------------------:|--------------------|------|--------------------------|------|
| `Box plot`              |        Box plot        | Ящик с усами       | 2d   | y (groups), pie (labels) | full |
| `Violin`                |         Violin         | Скрипичная         | 2d   | y (groups), pie          | full |
| `Strip plot`            |         Strip          | Стрип              | 2d   | y (groups), pie          | full |
| `Ridge plot`            |    Ridge (joyplot)     | Гребень            | 2d   | y (groups), pie          | full |
| `Raincloud plot`        |       Raincloud        | Дождевое облако    | 2d   | y (groups), pie          | —    |
| `Beanplot`              |        Beanplot        | Боб                | 2d   | y (groups), pie          | —    |
| `Swarm plot`            |         Swarm          | Рой                | 2d   | y (groups), pie          | full |
| `Cherry blossom plot`   |     Cherry blossom     | Сакура             | 2d   | y (groups), pie          | —    |
| `Dot-and-whisker`       |    Dot-and-whisker     | Точка-усы          | 2d   | y (groups), pie          | —    |
| `Q-Q plot`              |        Q-Q plot        | Квант-квант        | 2d   | y (sample)               | —    |
| `ECDF`                  |          ECDF          | Эмпирич. функция   | 2d   | y (sample)               | full |
| `Hexbin`                |         Hexbin         | Гексагоны          | 2d   | x, y, bins               | —    |
| `Сезонная декомпозиция` | Seasonal decomposition | Декомпозиция       | 2d   | x, y, bins (period)      | —    |
| `Rolling statistics`    |     Rolling stats      | Скольз. статистика | 2d   | x, y, bins (window)      | —    |

## 2D · Финансовые и проектные

| ID                 | EN               | RU              | Proj | Fields                          | HTML |
|--------------------|------------------|-----------------|------|---------------------------------|------|
| `Водопад`          | Waterfall        | Водопад         | 2d   | x, y, pie                       | full |
| `Гант`             | Gantt            | Гант            | 2d   | x (start), y (dur), pie, colors | full |
| `Свечи (OHLC)`     | Candlestick      | Свечи           | 2d   | x, box (O;H;L;C)                | full |
| `Renko`            | Renko            | Ренко           | 2d   | y, bins (brick)                 | —    |
| `Point-and-Figure` | Point-and-Figure | Крестики-нолики | 2d   | y, bins (box)                   | —    |
| `Диаграмма Парето` | Pareto           | Парето          | 2d   | x (labels), y                   | full |

## 2D · Сетевые и иерархические

| ID                      | EN                 | RU                      | Proj | Fields                           | HTML |
|-------------------------|--------------------|-------------------------|------|----------------------------------|------|
| `Сетевой график`        | Network            | Сеть                    | 2d   | z (`A-B; B-C`)                   | —    |
| `Hive plot`             | Hive               | Улей                    | 2d   | z (`A-B; …`)                     | —    |
| `Arc diagram`           | Arc                | Дуги                    | 2d   | z (`A-B; …`)                     | —    |
| `Дерево (tree diagram)` | Tree               | Дерево                  | 2d   | z (`parent-child; …`)            | —    |
| `Radial tree 3D`        | Radial tree 3D     | Радиальное дерево       | 3d   | x (z-offset), z (`p-c; …`)       | —    |
| `Sankey`                | Sankey             | Санкей                  | 2d   | y (flows), pie                   | —    |
| `Alluvial diagram`      | Alluvial           | Аллювиальная            | 2d   | z (matrix), x (`dst1;dst2`), pie | —    |
| `Chord`                 | Chord              | Хордовая                | 2d   | z (square matrix), pie           | —    |
| `Adjacency matrix`      | Adjacency matrix   | Матрица смежности       | 2d   | z (square matrix), pie           | —    |
| `Дендрограмма`          | Dendrogram         | Дендрограмма            | 2d   | z (matrix), pie                  | —    |
| `Cluster dendrogram`    | Cluster dendrogram | Кластерная дендрограмма | 2d   | z (matrix)                       | —    |
| `Circle packing`        | Circle packing     | Упаковка кругов         | 2d   | x (labels), y (sizes)            | —    |
| `Mapper algorithm`      | Mapper             | Mapper                  | 2d   | z (matrix), bins                 | —    |

## 2D · Матричные поля

| ID              | EN            | RU             | Proj | Fields                              | HTML |
|-----------------|---------------|----------------|------|-------------------------------------|------|
| `Heatmap`       | Heatmap       | Тепловая карта | 2d   | z (matrix)                          | full |
| `Contour`       | Contour       | Изолинии       | 2d   | z (matrix)                          | —    |
| `Imshow`        | Image         | Изображение    | 2d   | z (matrix)                          | —    |
| `Isopleth`      | Isopleth      | Изоплета       | 2d   | z (matrix), bins                    | —    |
| `Isosurface 3D` | Isosurface 3D | Изоповерхность | 3d   | z (matrix), bins                    | —    |
| `Stream plot`   | Stream plot   | Потоки         | 2d   | x, y, z (U-matrix), yerr (V-matrix) | —    |
| `Streamlines`   | Streamlines   | Линии тока     | 2d   | x, y, z (U), yerr (V), bins         | —    |
| `Quiver`        | Quiver        | Векторы        | 2d   | x, y, z (U), yerr (V)               | —    |
| `3D Quiver`     | Quiver 3D     | Векторы 3D     | 3d   | x, y, z, yerr (U)                   | —    |

## 2D · Радиотехника

| ID                      | EN            | RU                | Proj | Fields                      | HTML |
|-------------------------|---------------|-------------------|------|-----------------------------|------|
| `Bode plot`             | Bode          | Боде              | 2d   | x (freq), y (dB), z (phase) | —    |
| `Smith chart`           | Smith         | Смит              | 2d   | x (Re) + y (Im) или z (2×N) | —    |
| `Nyquist plot`          | Nyquist       | Найквист          | 2d   | x (ω), y (Re), z (Im)       | —    |
| `Root locus`            | Root locus    | Корневой годограф | 2d   | x (num), y (den), bins      | —    |
| `Constellation diagram` | Constellation | Созвездие         | 2d   | x (I), y (Q), z (Rx-pairs)  | —    |

## 2D · ML / биоинформатика

| ID                | EN             | RU              | Proj | Fields                      | HTML |
|-------------------|----------------|-----------------|------|-----------------------------|------|
| `Volcano plot`    | Volcano        | Вулкан          | 2d   | x (logFC), y (-log10p)      | —    |
| `ROC curve`       | ROC            | ROC-кривая      | 2d   | y (true labels), z (scores) | —    |
| `Manhattan plot`  | Manhattan      | Манхэттен       | 2d   | x, y, z (chrom)             | full |
| `MA plot`         | MA             | MA              | 2d   | x (A), y (M)                | full |
| `Recurrence plot` | Recurrence     | Рекуррентная    | 2d   | y, bins (m)                 | —    |
| `Cobweb plot`     | Cobweb         | Паутина         | 2d   | x (formula), y (`x0; N`)    | —    |
| `Poincaré plot`   | Poincaré       | Пуанкаре        | 2d   | y, bins (τ)                 | —    |
| `Phase portrait`  | Phase portrait | Фазовый портрет | 2d   | x, y, z (optional field)    | —    |

## 2D · Гео / метео / научные

| ID                      | EN          | RU                 | Proj  | Fields                               | HTML |
|-------------------------|-------------|--------------------|-------|--------------------------------------|------|
| `Choropleth`            | Choropleth  | Хороплет           | 2d    | z (matrix), pie (rows), x (cols)     | —    |
| `Flow map`              | Flow map    | Карта потоков      | 2d    | x, y, pie (node names), z (`A-B; …`) | —    |
| `Cartogram`             | Cartogram   | Картограмма        | 2d    | x (labels), y (sizes)                | —    |
| `Dot density map`       | Dot density | Точечная плотность | 2d    | z (matrix)                           | —    |
| `Hodograph`             | Hodograph   | Ходограф           | 2d    | x (U), y (V)                         | —    |
| `Роза ветров`           | Wind rose   | Роза ветров        | polar | x (dir°), y (speed), bins            | —    |
| `Skew-T log-P`          | Skew-T      | Аэрологическая     | 2d    | x (p), y (T), z (Td)                 | —    |
| `Thermodynamic diagram` | Emagram     | Термодинамическая  | 2d    | x (p), y (T), z (Td)                 | —    |
| `Диаграмма Вороного`    | Voronoi     | Вороной            | 2d    | x, y                                 | —    |
| `Выпуклая оболочка`     | Convex hull | Выпуклая оболочка  | 2d    | x, y                                 | —    |
| `Alpha shape`           | Alpha shape | Альфа-форма        | 2d    | x, y, bins (α)                       | —    |

## 2D · Специальные / рейтинги / сравнение

| ID                          | EN                  | RU                   | Proj  | Fields                            | HTML               |
|-----------------------------|---------------------|----------------------|-------|-----------------------------------|--------------------|
| `Радиальная`                | Radial bar          | Радиальная           | polar | x (angle°), y                     | full               |
| `Полярный scatter`          | Polar scatter       | Полярные точки       | polar | x (angle°), y                     | full               |
| `Полярная теплокарта`       | Polar heatmap       | Полярная тепло       | polar | x, y, z (matrix)                  | —                  |
| `Treemap`                   | Treemap             | Древовидная карта    | 2d    | y, pie, parents                   | full (только HTML) |
| `Sunburst`                  | Sunburst            | Солнечные лучи       | 2d    | y, pie, parents                   | full (только HTML) |
| `Dot plot`                  | Dot plot            | Точечная (категории) | 2d    | x (labels), y                     | —                  |
| `Lollipop`                  | Lollipop            | Леденец              | 2d    | x, y                              | —                  |
| `Пирамида`                  | Pyramid             | Пирамида             | 2d    | x, y, z                           | —                  |
| `Sparkline`                 | Sparkline           | Спарклайн            | 2d    | x, y                              | —                  |
| `Cycle plot`                | Cycle plot          | Циклическая          | 2d    | x, y, z (group)                   | —                  |
| `Bump chart`                | Bump chart          | Bump                 | 2d    | x (times), z (matrix), pie        | —                  |
| `Slopegraph`                | Slopegraph          | Наклон               | 2d    | x (`До,После`), y, z, pie         | —                  |
| `Dumbbell plot`             | Dumbbell            | Гантель              | 2d    | x (labels), y (start), z (end)    | —                  |
| `Bar of pie`                | Bar of pie          | Столбец + пирог      | 2d    | x (labels), y                     | —                  |
| `Pie of pie`                | Pie of pie          | Пирог + пирог        | 2d    | x (labels), y                     | full               |
| `Ribbon plot 2D`            | Ribbon 2D           | Лента                | 2d    | x, y, z                           | full               |
| `Bullet chart`              | Bullet              | Пулевая              | 2d    | x (KPI), y (`target;warning;max`) | —                  |
| `Funnel chart`              | Funnel              | Воронка              | 2d    | x (stages), y                     | —                  |
| `Календарная теплокарта`    | Calendar heatmap    | Календарь            | 2d    | x (unix time?), y                 | —                  |
| `Диаграмма бифуркаций`      | Bifurcation         | Бифуркация           | 2d    | x (`rmin,rmax`), y (`x0`), bins   | —                  |
| `Parallel coordinates`      | Parallel coords     | Параллельные         | 2d    | z (matrix), pie (axis names)      | —                  |
| `Radar chart`               | Radar               | Радар                | polar | z (matrix), pie (axes)            | —                  |
| `Спидометр`                 | Gauge               | Спидометр            | 2d    | x (`min,max`), y (value)          | —                  |
| `Вафельная диаграмма`       | Waffle              | Вафля                | 2d    | y, pie, colors, bins (grid)       | —                  |
| `Сосулька (icicle)`         | Icicle              | Сосулька             | 2d    | y, pie (names), x (`parents; …`)  | —                  |
| `Диаграмма Аргана`          | Argand              | Арган                | 2d    | x (Re), y (Im), z (labels)        | —                  |
| `Диаграмма Тейлора`         | Taylor              | Тейлор               | polar | x (ref std), z (`std; corr`)      | —                  |
| `Горизонтальная столбчатая` | Horizontal bar      | Гориз. столбчатая    | 2d    | x, y, yerr                        | full               |
| `Горизонтальная линия`      | Horizontal line     | Гориз. линия         | 2d    | x, y, fill                        | full               |
| `Топографический профиль`   | Topographic profile | Топопрофиль          | 2d    | x, y, bins                        | full               |
| `Вейвлет-скейлограмма`      | Wavelet scalogram   | Вейвлет              | 2d    | x, y, z (wavelet name), bins (fs) | —                  |

## 3D · Базовые

| ID                | EN           | RU              | Proj | Fields           | HTML |
|-------------------|--------------|-----------------|------|------------------|------|
| `3D Линия`        | Line 3D      | 3D линия        | 3d   | x, y, z, fill    | full |
| `3D Точечная`     | Scatter 3D   | 3D точки        | 3d   | x, y, z, glow    | full |
| `3D Столбчатая`   | Bar 3D       | 3D столбчатая   | 3d   | x, y, z          | —    |
| `3D Гистограмма`  | Histogram 3D | 3D гистограмма  | 3d   | x, y, bins       | —    |
| `3D Круговая`     | Pie 3D       | 3D круговая     | 3d   | y, colors        | —    |
| `3D Поверхность`  | Surface 3D   | 3D поверхность  | 3d   | x, y, z (matrix) | full |
| `3D Сетка`        | Mesh 3D      | 3D сетка        | 3d   | x, y, z (matrix) | full |
| `3D Полигон`      | Polygon 3D   | 3D полигон      | 3d   | x, y, z          | full |
| `3D Триангуляция` | Trisurf 3D   | 3D триангуляция | 3d   | x, y, z          | full |

## 3D · Расширенные

| ID                         | EN           | RU         | Proj | Fields                          | HTML |
|----------------------------|--------------|------------|------|---------------------------------|------|
| `3D Quiver`                | Quiver 3D    | 3D векторы | 3d   | x, y, z, yerr (U)               | —    |
| `Ribbon plot 3D`           | Ribbon 3D    | 3D лента   | 3d   | x, y, z, bins (width)           | —    |
| `Waterfall spectrogram 3D` | Waterfall 3D | 3D водопад | 3d   | x, y, z (matrix), fill          | —    |
| `Riemann surface 3D`       | Riemann 3D   | Риман      | 3d   | x (`rmin,rmax`), y, z (formula) | —    |
| `Joyplot 3D`               | Joyplot 3D   | 3D гребень | 3d   | y (groups), pie (labels)        | —    |

---

## Что нужно знать при добавлении нового типа

1. Добавьте ID в `INTERNAL_TYPES` в `grapheditor/translator.py`.
2. Добавьте ключ в `TYPE_TO_KEY` (там же).
3. Добавьте этот ключ во все 20 файлов `translations/*.py`.
4. Добавьте ветку в `_create_artist.py`.
5. Добавьте разбор данных в `_add_graph` в `_extras.py`.
6. **Добавьте строку в эту таблицу** (категория, проекция, поля, HTML-статус).
7. Запустите `python tools/check_types.py` — покажет, если что-то забыли (см. ниже).