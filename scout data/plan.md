Источник данных и raw-слой
1. Источник
API: Launch Library 2 (LL2), The Space Devs, версия 2.3.0
Боевой хост: https://ll.thespacedevs.com/
Dev-хост: https://lldev.thespacedevs.com/ (данные устаревшие и неполные, для отладки кода, жёсткого лимита нет)
Документация: https://ll.thespacedevs.com/docs/
2. Важное из документации
Тема	Факт
Лимит	15 запросов в час без ключа. Решение: для проекта этого хватает, ключ не нужен.
Размер страницы	limit до 100
Пагинация	В ответе count, next, previous; следующая страница берётся из next
Режимы	?mode=list, normal, detailed. Используем normal.
Будущие запуски	/2.3.0/launches/upcoming/ (включает также запуски за последние 24 часа, есть параметр hide_recent_previous)
Прошедшие запуски	/2.3.0/launches/previous/
Сортировка	ordering по net и last_updated (по возрастанию и убыванию)
Фильтры	У /launches/ много фильтров. Точные имена фильтров по дате: уточнить в доке.
Формат	?format=json
Объём истории	Порядка 7,5 тыс. прошедших запусков (по сторонним описаниям), около 76 страниц по 100. При лимите это около 5 часов бэкфилла, грузить порциями.
3. Что получаем в ответе

Пример: GET /2.3.0/launches/upcoming/?limit=10, ответ в режиме normal, count: 477.

Обёртка ответа:

{ count, next, previous, results: [ launch, ... ] }

Один элемент results (запуск), блоки верхнего уровня:

launch
├── id (uuid), url, name, slug, response_mode, launch_designator
├── status               {id, name, abbrev, description}
├── last_updated, net, net_precision, window_start, window_end
├── image                {id, name, image_url, thumbnail_url, credit, license, single_use, variants}
├── infographic, probability, weather_concerns, failreason, hashtag, webcast_live
├── launch_service_provider   {id, url, name, abbrev, type}
├── rocket
│   ├── id               (конкретный экземпляр ракеты)
│   └── configuration    {id, url, name, full_name, variant, families[]}
├── mission              {id, name, type, description, image, orbit, agencies[], info_urls[], vid_urls[]}
│   └── agencies[]       (заказчики; вложены полные описания, страны, логотипы, соцсети, статистика)
├── pad                  {id, name, latitude, longitude, country, agencies[], image, wiki_url, map_url, ...}
│   └── location         {id, name, latitude, longitude, country, timezone_name, celestial_body{...}, ...}
├── program[]            (вложены описания программы и агентства)
└── *_launch_attempt_count, *_launch_attempt_count_year (счётчики)

Особенности структуры:

Вложенные объекты (площадка, космодром, агентства, программы) повторяются в каждом запуске целиком.
rocket.id это экземпляр, rocket.configuration.id это тип ракеты (например 164 = Falcon 9 Block 5).
Координаты есть и у pad, и у pad.location, значения отличаются.
launch_service_provider внутри запуска без страны; страна есть у pad.country и у mission.agencies[].country.
Встречаются Unknown Pad, Unknown Payload и null в image, description, map_url.
Данные запуска меняются со временем (net, status), поэтому у каждой записи есть last_updated.
4. Raw-слой

Принцип: в raw кладётся всё, что вернул API, без отбора и преобразований. Фильтрация полей делается при построении core.

Одна строка = один запуск (один элемент results), денормализованно: вложенные объекты остаются внутри.

Черновик таблицы raw.launches:

Колонка	Тип	Содержимое
launch_id	uuid, PK	id запуска
payload	JSONB	элемент results целиком, как пришёл
source_endpoint	text	upcoming или previous
api_last_updated	timestamptz	last_updated из payload (для проверки, свежее ли пришедшая версия)
fetched_at	timestamptz	когда загрузили

Правила загрузки:

Идемпотентный upsert по launch_id: запись заменяется, если last_updated в ответе новее сохранённого.
Запуск, ушедший из upcoming в previous, обновляется той же строкой.
Обёртку ответа (count, next) в таблицу не кладём, она нужна только для пагинации.
Код разрабатываем на lldev, боевой API используем для реальной загрузки.