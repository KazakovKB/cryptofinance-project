import dash
import logging
from dash import dcc
from dash import html
import plotly.graph_objs as go
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output, State
import backend as bc
from plotly.subplots import make_subplots
from datetime import datetime, timedelta

# Инициализация Dash приложения с использованием стилей Bootstrap для оформления
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

# Элементы управления интерфейса приложения
data = {
    'symbol-dropdown': ['BTCUSDT'],
    'source-dropdown': ['Binance Futures'],
    'indicator-dropdown': ['Volume', 'Delta', 'Cumulative Delta'],
    'type-dropdown': [
        'Объём (candle)',
        'Кол-во сделок (candle)',
        'Дельта (candle)',
        'Объём (price)',
        'Кол-во сделок (price)',
        'Дельта (price)'
    ]
}

# Настройка макета приложения, определяющего структуру и содержание веб-страницы Dashboard
layout_dashboard = html.Div([
    html.Div([
        dbc.Row([dbc.Col(html.H3("Книга ордеров", className="mb-2 text-center", style={'color': '#fd7e14'}),
                         width=12, className="d-flex justify-content-center")]),

        dbc.Row([
            dbc.Col(
                dbc.Card([
                    dbc.CardHeader(
                        html.H6("Spread", className="mb-0"), className="bg-dark text-white"
                    ),
                    dbc.CardBody([
                        html.H1(id="spread-value", className="card-title")
                    ], className="bg-dark text-white")

                ], className="shadow-lg", style={'border': '4px #1e2027'}), width=6, style={'padding-right': '2px'}
            ),
            dbc.Col(
                dbc.Card([
                    dbc.CardHeader(
                        html.H6("Bid/Ask Ratio", className="mb-0"), className="bg-dark text-white"
                    ),
                    dbc.CardBody([
                        html.H1(id="bid-ask-ratio-value", className="card-title")
                    ], className="bg-dark text-white")

                ], className="shadow-lg", style={'border': '4px #1e2027'}), width=6, style={'padding-left': '2px'}
            )
        ], style={'margin-bottom': '4px'}),

        dbc.Row([
            dbc.Col(
                dbc.Card([
                    dbc.CardHeader([
                        dbc.Row([
                            dbc.Col(
                                html.H6("Volume By Price", className="mb-0 mt-2"),
                                width=8, className="bg-dark text-white"
                            ),
                            dbc.Col(
                                html.Div([
                                    dbc.Button(
                                        "Настройки", id="setup-graph-orderbook", className="btn-custom", n_clicks=0
                                    ),
                                    dbc.Modal([
                                        dbc.ModalHeader(dbc.ModalTitle("Фильтры"), className='modal-custom'),
                                        dbc.ModalBody([
                                            html.Label("Глубина:", className="text-white"),
                                            dcc.Dropdown(
                                                id='orderbook-depth-dropdown',
                                                options=[
                                                    {'label': '+/- 30%', 'value': 0.3},
                                                    {'label': '+/- 50%', 'value': 0.5},
                                                ],
                                                value=0.3, searchable=False, style={'width': '100%'}
                                            ),
                                            html.Br(),
                                            html.Label("Ценовой шаг:", className="text-white"),
                                            dcc.Dropdown(
                                                id='price-step-dropdown',
                                                options=[
                                                    {'label': '$500', 'value': 500},
                                                    {'label': '$1000', 'value': 1000},
                                                ],
                                                value=1000, searchable=False,
                                                style={'width': '100%'}
                                            )
                                        ], className='modal-custom'),
                                        dbc.ModalFooter(
                                            dbc.Button(
                                                "Применить",
                                                id="apply-filters-orderbook",
                                                className="ml-auto btn-custom"
                                            ), className='modal-custom'
                                        )
                                    ], id="modal-orderbook", is_open=False)
                                ], className="d-flex justify-content-end"), width=4, className="bg-dark text-white")
                        ]),
                    ], className="bg-dark text-white"),

                    dbc.CardBody([dcc.Graph(id='orderbook-graph')], className="bg-dark text-white")

                ], className="shadow-lg", style={'border': '4px #1e2027'}), width=12
            )
        ])
    ], style={'backgroundColor': '#1e2027', 'padding': '4px', 'margin-bottom': '24px'}),

    html.Div([
        dbc.Row([
            dbc.Col(
                html.H3("Сделки", className="mb-2 text-center", style={'color': '#fd7e14'}), width=12,
                className="d-flex justify-content-center"
            )
        ]),

        dbc.Row([
            dbc.Col(
                dbc.Card([
                    dbc.CardHeader(
                        html.H6("Volume BTC", className="mb-0"), className="bg-dark text-white"
                    ),
                    dbc.CardBody([
                        html.H1(id="volume-trades", className="card-title"),
                        html.P(id="volume-trades-add")
                    ], className="bg-dark text-white", style={'padding-bottom': '0px'})

                ], className="shadow-lg", style={'border': '4px #1e2027'}), width=6,
                style={'padding-right': '2px'}
            ),
            dbc.Col(
                dbc.Card([
                    dbc.CardHeader(
                        html.H6("Trades", className="mb-0"), className="bg-dark text-white"
                    ),
                    dbc.CardBody([
                        html.H1(id="count-trades", className="card-title"),
                        html.P(id="count-trades-add")
                    ], className="bg-dark text-white", style={'padding-bottom': '0px'})

                ], className="shadow-lg", style={'border': '4px #1e2027'}), width=6, style={'padding-left': '2px'}
            ),
        ], style={'margin-bottom': '4px'}),

        dbc.Row([
            dbc.Col(
                dbc.Card([
                    dbc.CardHeader([
                        dbc.Row([
                            dbc.Col(
                                dcc.Dropdown(
                                    id='graph-selector',
                                    options=[
                                        {'label': 'Delta', 'value': 'delta'},
                                        {'label': 'Buy/Sell Ratio', 'value': 'ratio'},
                                        {'label': 'Volume By Price', 'value': 'dist'}
                                    ],
                                    value='delta',
                                    multi=False,
                                    searchable=False
                                ), width=8),
                            dbc.Col(html.Div([
                                dbc.Button(
                                    "Настройки", id="setup-graph-trades", className="btn-custom", n_clicks=0
                                ),
                                dbc.Modal([
                                    dbc.ModalHeader(dbc.ModalTitle("Фильтры"), className='modal-custom'),
                                    dbc.ModalBody([
                                        html.Label("Количество дней", className='text-white'),
                                        dcc.Slider(1, 7, 1, value=4, id="slider-days-trades",
                                                   marks={i: str(i) for i in range(1, 8)},
                                                   tooltip={"placement": "bottom", "always_visible": True}),
                                        html.Br(),
                                        html.Label("Тип данных", className='text-white'),
                                        dcc.Dropdown(
                                            id="type-data-trades",
                                            options=[
                                                {'label': 'Сделки', 'value': 'COUNT'},
                                                {'label': 'Объем', 'value': 'SUM'}
                                            ],
                                            value='SUM',
                                            multi=False,
                                            searchable=False
                                        )
                                    ], className='modal-custom'),
                                    dbc.ModalFooter(
                                        dbc.Button(
                                            "Применить", id="apply-filters-trades",
                                            className="ml-auto btn-custom"
                                        ), className='modal-custom'
                                    )
                                ], id="modal-trades", is_open=False)
                            ], className="d-flex justify-content-end"), width=4)
                        ])
                    ], className="bg-dark text-white"),
                    dbc.CardBody([dcc.Graph(id='trades-graph')], className='bg-dark text-white')
                ], className="shadow-lg", style={'border': '4px #1e2027'}), width=12
            )
        ])
    ], style={'backgroundColor': '#1e2027', 'padding': '4px', 'margin-bottom': '24px'}),

    html.Div([
        dbc.Row([
            dbc.Col(
                html.H3("Рыночная Аналитика", className="mb-2 text-center", style={'color': '#fd7e14'}), width=12,
                className="d-flex justify-content-center"
            )
        ]),

        dbc.Row([
            dbc.Col(
                dbc.Card([
                    dbc.CardHeader(
                        html.H6("Liquidation", className="mb-0"), className="bg-dark text-white"
                    ),
                    dbc.CardBody([
                        html.H1(id="volume-liquidation", className="card-title"),
                        html.P(id="liquidation-add")
                    ], className="bg-dark text-white", style={'padding-bottom': '0px'})

                ], className="shadow-lg", style={'border': '4px #1e2027'}), width=6,
                style={'padding-right': '2px'}
            ),
            dbc.Col(
                dbc.Card([
                    dbc.CardHeader(
                        html.H6("Open Interest", className="mb-0"), className="bg-dark text-white"
                    ),
                    dbc.CardBody([
                        html.H1(id="value-oi", className="card-title"),
                        html.P(id="oi-add")
                    ], className="bg-dark text-white", style={'padding-bottom': '0px'})

                ], className="shadow-lg", style={'border': '4px #1e2027'}), width=6, style={'padding-left': '2px'}
            ),
        ], style={'margin-bottom': '4px'}),

        dbc.Row([
            dbc.Col(
                dbc.Card([
                    dbc.CardHeader([
                        dbc.Row([
                            dbc.Col(
                                dcc.Dropdown(
                                    id='graph-selector-analysis',
                                    options=[
                                        {'label': 'Volatility Price', 'value': 'kline'},
                                        {'label': 'Long/Short Ratio', 'value': 'longShortRatio'},
                                        {'label': 'Liquidation Rate', 'value': 'liquidationRate'}
                                    ],
                                    value='kline',
                                    multi=False,
                                    searchable=False
                                ), width=8),
                            dbc.Col(html.Div([
                                dbc.Button(
                                    "Настройки", id="setup-graph-analysis", className="btn-custom", n_clicks=0
                                ),
                                dbc.Modal([
                                    dbc.ModalHeader(dbc.ModalTitle("Фильтры"), className='modal-custom'),
                                    dbc.ModalBody([
                                        html.Label("Количество дней", className='text-white'),
                                        dcc.Slider(1, 7, 1, value=4, id="slider-days-analysis",
                                                   marks={i: str(i) for i in range(1, 8)},
                                                   tooltip={"placement": "bottom", "always_visible": True}),
                                        html.Br(),
                                        html.Label("Long/Short", className='text-white'),
                                        dcc.Dropdown(
                                            id="type-data-analysis",
                                            options=[
                                                {'label': 'Account', 'value': 'global'},
                                                {'label': 'Position', 'value': 'position'}
                                            ],
                                            value='global',
                                            multi=False,
                                            searchable=False
                                        )
                                    ], className='modal-custom'),
                                    dbc.ModalFooter(
                                        dbc.Button(
                                            "Применить", id="apply-filters-analysis",
                                            className="ml-auto btn-custom"
                                        ), className='modal-custom'
                                    )
                                ], id="modal-analysis", is_open=False)
                            ], className="d-flex justify-content-end"), width=4)
                        ])
                    ], className="bg-dark text-white"),
                    dbc.CardBody([dcc.Graph(id='analysis-graph')], className='bg-dark text-white')
                ], className="shadow-lg", style={'border': '4px #1e2027'}), width=12
            )
        ], style={'margin-bottom': '4px'}),

        dbc.Row([
            dbc.Col(
                dbc.Card([
                    dbc.CardHeader([
                        dbc.Row([
                            dbc.Col(
                                dcc.Dropdown(
                                    id='graph-selector-analysis-2',
                                    options=[
                                        {'label': 'Funding Rate', 'value': 'funding'},
                                        {'label': 'Open Interest', 'value': 'oi'},
                                        {'label': 'Liquidation By Price', 'value': 'liquidationByPrice'}
                                    ],
                                    value='funding',
                                    multi=False,
                                    searchable=False
                                ), width=8),
                            dbc.Col(html.Div([
                                dbc.Button(
                                    "Настройки", id="setup-graph-analysis-2", className="btn-custom", n_clicks=0
                                ),
                                dbc.Modal([
                                    dbc.ModalHeader(dbc.ModalTitle("Фильтры"), className='modal-custom'),
                                    dbc.ModalBody([
                                        html.Label("Количество дней", className='text-white'),
                                        dcc.Slider(1, 7, 1, value=4, id="slider-days-analysis-2",
                                                   marks={i: str(i) for i in range(1, 8)},
                                                   tooltip={"placement": "bottom", "always_visible": True})
                                    ], className='modal-custom'),
                                    dbc.ModalFooter(
                                        dbc.Button(
                                            "Применить", id="apply-filters-analysis-2",
                                            className="ml-auto btn-custom"
                                        ), className='modal-custom'
                                    )
                                ], id="modal-analysis-2", is_open=False)
                            ], className="d-flex justify-content-end"), width=4)
                        ])
                    ], className="bg-dark text-white"),
                    dbc.CardBody([dcc.Graph(id='analysis-graph-2')], className='bg-dark text-white')
                ], className="shadow-lg", style={'border': '4px #1e2027'}), width=12
            )
        ])
    ], style={'backgroundColor': '#1e2027', 'padding': '4px'}),
    html.Br(),

    # Добавляем компонент для автоматического обновления
    dcc.Interval(
        id='interval-component',
        interval=10 * 1000,  # в миллисекундах, 10 секунд между обновлениями
        n_intervals=0
    )
])

# Настройка макета приложения, определяющего структуру и содержание веб-страницы Terminal
layout_terminal = html.Div([
    html.Div([
        dbc.Row([dbc.Col(html.H3("Свечной график", className="mb-2 text-center", style={'color': '#fd7e14'}),
                         width=12, className="d-flex justify-content-center")]),

        dbc.Row([
            dbc.Col(
                dbc.Card([
                    dbc.CardHeader(
                        html.H6("Price", className="mb-0"), className="bg-dark text-white"
                    ),
                    dbc.CardBody([
                        html.H1(id="price-value", className="card-title")
                    ], className="bg-dark text-white")

                ], className="shadow-lg", style={'border': '4px #1e2027'}), width=12
            )
        ], style={'margin-bottom': '4px'}),

        dbc.Row([
            dbc.Col(
                dbc.Card([
                    dbc.CardHeader([
                        dbc.Row([
                            dbc.Col(
                                html.H6("Chart", className="mb-0 mt-2"),
                                width=4, className="bg-dark text-white"
                            ),

                            dbc.Col(html.Div([
                                dbc.Button(
                                    "Cluster", id="cluster-search", className="btn-custom", n_clicks=0
                                ),
                                dbc.Modal([
                                    dbc.ModalHeader(dbc.ModalTitle("Cluster Search"), className='modal-custom'),
                                    dbc.ModalBody([
                                        html.Label("Тип", className='text-white'),
                                        dcc.Dropdown(
                                            id="type-dropdown",
                                            options=[
                                                {"label": x, "value": x}
                                                for x in data['type-dropdown']
                                            ],
                                            multi=False,
                                            searchable=False
                                        ),
                                        html.Br(),
                                        html.Label("Фильтр", htmlFor="filter-slider-cluster", className='text-white'),
                                        dcc.Slider(
                                            id='filter-slider-cluster',
                                            min=0,
                                            max=4,
                                            value=4,
                                            marks={0: '>95%', 1: '>96%', 2: '>97%', 3: '>98%', 4: '>99%'},
                                            step=None
                                        ),
                                        html.Br(),
                                        dbc.Accordion([
                                            dbc.AccordionItem([
                                                dcc.Markdown(
                                                    "Cluster Search - предназначена для выявления"
                                                    " необычных торговых активностей на рынке криптовалют."
                                                    " Она фокусируется на ключевых показателях, таких как объем"
                                                    " торгов, количество транзакций или дельта."
                                                )
                                            ], title="Что это за функция?"),

                                            dbc.AccordionItem([
                                                dcc.Markdown(
                                                    "Cluster Search - согласно выбранным параметрам "
                                                    "ищет данные показатель которых больше чем у выбранного"
                                                    " порога. Такой подход помогает выделить торги,"
                                                    " которые отличаются своими высокими показателями,"
                                                    " что указывает на потенциальные аномалии."
                                                )
                                            ], title="Как это работает?")
                                        ], active_item=None, className='accordion-custom'),
                                    ], className='modal-custom'),

                                    dbc.ModalFooter(
                                        dbc.Button(
                                            "Применить", id="apply-cluster-search", className="ml-auto btn-custom"
                                        ), className='modal-custom'
                                    )
                                ], id="modal-cluster_search", is_open=False)
                            ]), width=4),

                            dbc.Col(html.Div([
                                dbc.Button("Настройки", id="setup-terminal", n_clicks=0, className="btn-custom"),
                                dbc.Offcanvas([
                                    html.Label("Торговая пара:", htmlFor="symbol-dropdown", className='text-white'),
                                    dcc.Dropdown(
                                        id="symbol-dropdown",
                                        options=[
                                            {"label": x, "value": x}
                                            for x in data['symbol-dropdown']
                                        ],
                                        value='BTCUSDT',
                                        multi=False,
                                        searchable=False
                                    ),
                                    html.Br(),
                                    html.Label("Источник данных:", className='text-white'),
                                    dcc.Dropdown(
                                        id="source-dropdown",
                                        options=[
                                            {"label": x, "value": x}
                                            for x in data['source-dropdown']
                                        ],
                                        value='Binance Futures',
                                        multi=False,
                                        searchable=False
                                    ),
                                    html.Br(),
                                    html.Label("Таймфрейм:", className='text-white'),
                                    dcc.Slider(
                                        id='timeframe-slider',
                                        min=0,
                                        max=3,
                                        value=1,
                                        marks={0: '1h', 1: '2h', 2: '4h', 3: '1d'},
                                        step=None
                                    ),
                                    html.Br(),
                                    html.Label("Количество дней:", className='text-white'),
                                    dcc.Slider(
                                        id="amount-days-slider", min=1, max=7, step=1, value=2,
                                        marks={i: str(i) for i in range(1, 8)},
                                        tooltip={"placement": "bottom", "always_visible": True}
                                    ),
                                    html.Br(),
                                    dbc.ModalFooter(
                                        dbc.Button(
                                            "Применить", id="apply-filters-candle", className="ml-auto btn-custom"
                                        ), className='modal-custom'
                                    )
                                ], id="offCanvas", title="Фильтры", is_open=False, className='offCanvas-custom')
                            ], className="d-flex justify-content-end"), width=4)
                        ]),
                        html.Br(),
                        dbc.Row([
                            dbc.Col(html.Div([
                                html.Label("Indicators:", className='text-white'),
                                dcc.Dropdown(
                                    id="indicator-dropdown",
                                    value=[],
                                    options=[
                                        {"label": x, "value": x}
                                        for x in data['indicator-dropdown']
                                    ],
                                    multi=True,
                                    searchable=False
                                )
                            ]), width=12)
                        ])
                    ], className="bg-dark text-white"),
                    dbc.CardBody([dcc.Graph(id='candle-graph')], className='bg-dark text-white')
                ], className="shadow-lg", style={'border': '4px #1e2027'}), width=12
            )
        ])
    ], style={'backgroundColor': '#1e2027', 'padding': '4px'}),
    html.Br(), html.Br(),

    # Добавляем компонент для автоматического обновления
    dcc.Interval(
        id='interval-component-2',
        interval=5 * 1000,  # в миллисекундах, 1 секунда между обновлениями
        n_intervals=0
    )
])

# Настройка макета приложения
app.layout = html.Div([
    dbc.Container([
        dbc.Row([
            dbc.Col(
                dbc.Tabs(id="tabs", className="nav nav-tabs", children=[
                    dbc.Tab(label='Dashboard', tab_id='tab-dashboard', children=[layout_dashboard]),
                    dbc.Tab(label='Terminal', tab_id='tab-terminal', children=[layout_terminal])
                ], active_tab='tab-dashboard'))
        ])
    ])
])


# === layout_dashboard === #
# Функции обратного вызова для управления отображением модального окна в дашборде
@app.callback(
    Output("modal-orderbook", "is_open"),
    [Input("setup-graph-orderbook", "n_clicks"),
     Input("apply-filters-orderbook", "n_clicks")],
    [State("modal-orderbook", "is_open")]
)
def toggle_modal_orderbook(n_open, n_apply, is_open):
    if n_open or n_apply:
        return not is_open
    return is_open


@app.callback(
    Output("modal-trades", "is_open"),
    [Input("setup-graph-trades", "n_clicks"),
     Input("apply-filters-trades", "n_clicks")],
    [State("modal-trades", "is_open")]
)
def toggle_modal_trades(n_open, n_apply, is_open):
    if n_open or n_apply:
        return not is_open
    return is_open


@app.callback(
    Output("modal-analysis", "is_open"),
    [Input("setup-graph-analysis", "n_clicks"),
     Input("apply-filters-analysis", "n_clicks")],
    [State("modal-analysis", "is_open")]
)
def toggle_modal_analysis(n_open, n_apply, is_open):
    if n_open or n_apply:
        return not is_open
    return is_open


@app.callback(
    Output("modal-analysis-2", "is_open"),
    [Input("setup-graph-analysis-2", "n_clicks"),
     Input("apply-filters-analysis-2", "n_clicks")],
    [State("modal-analysis-2", "is_open")]
)
def toggle_modal_analysis_2(n_open, n_apply, is_open):
    if n_open or n_apply:
        return not is_open
    return is_open


# Функции обратного вызова для регулярного обновления метрик дашборда
@app.callback(
    [Output('spread-value', 'children'),
     Output('bid-ask-ratio-value', 'children')],
    [Input('interval-component', 'n_intervals')]
)
def update_metrics_orderbook(n):
    spread = bc.get_orderbook_metrics('spread')
    ratio = bc.get_orderbook_metrics('ratio')

    return f"${spread['spread'].iloc[0]}", f"{ratio['bid_ask_ratio'].iloc[0]}"


@app.callback(
    [Output('volume-trades', 'children'),
     Output('volume-trades-add', 'children'),
     Output('count-trades', 'children'),
     Output('count-trades-add', 'children')],
    [Input('interval-component', 'n_intervals')]
)
def update_metrics_trades(n):
    volume = bc.get_trades_metrics('SUM', 'volume')

    volume_metric = ((volume['volume'] - volume['average']) / volume['volume'] * 100).round(2).iloc[0]
    if volume_metric > 0:
        volume_metric = f"+{volume_metric}% vs. AVG"
    else:
        volume_metric = f"{volume_metric}% vs. AVG"

    count = bc.get_trades_metrics('COUNT', 'volume')
    count_metric = ((count['volume'] - count['average']) / count['volume'] * 100).round(2).iloc[0]
    if count_metric > 0:
        count_metric = f"+{count_metric}% vs. AVG"
    else:
        count_metric = f"{count_metric}% vs. AVG"

    volume = volume['volume'].div(1000).astype(int).iloc[0]
    count = count['volume'].div(1000).astype(int).iloc[0]

    return f"{volume}K", volume_metric, f"{count}K", count_metric


@app.callback(
    [Output('volume-liquidation', 'children'),
     Output('liquidation-add', 'children'),
     Output('value-oi', 'children'),
     Output('oi-add', 'children')],
    [Input('interval-component', 'n_intervals')]
)
def update_metrics_analysis(n):
    liquidation = bc.get_liquidation_metrics(None, 'total_volume')

    curr_value = liquidation['total_quantity'].iloc[-1]
    avg_value = liquidation['total_quantity'].iloc[:-1].mean()

    pct_avg_value = (float(curr_value) - float(avg_value)) / float(avg_value) * 100
    output_pct = f'+{pct_avg_value:.2f}% vs. AVG' if pct_avg_value > 0 else f'{pct_avg_value:.2f}% vs. AVG'

    oi = bc.get_oi()
    oi_curr = oi['sumOpenInterest'].iloc[-1]
    oi_avg = oi['sumOpenInterest'].iloc[:-1].mean()

    oi_avg_pct = (float(oi_curr) - float(oi_avg)) / float(oi_avg) * 100
    output_oi_pct = f'+{oi_avg_pct:.2f}% vs. AVG' if oi_avg_pct > 0 else f'{oi_avg_pct:.2f}% vs. AVG'

    return f'{curr_value:.0f} BTC', output_pct, f'{oi_curr / 1000:.0f}K BTC', output_oi_pct


# Функции обратного вызова для динамического обновления графиков дашборда
@app.callback(
    Output('orderbook-graph', 'figure'),
    [Input('interval-component', 'n_intervals'),
     Input('orderbook-depth-dropdown', 'value'),
     Input('price-step-dropdown', 'value')]
)
def update_orderbook_graph(n, order_range, price_step):
    # Получение дистрибутивных метрик книги ордеров на основе заданного диапазона и шага цены
    dist = bc.get_orderbook_metrics('dist', order_range=order_range, price_step=price_step)
    # Фильтрация данных
    bid_data = dist[dist['order_type'] == 'bid']
    ask_data = dist[dist['order_type'] == 'ask']

    # Инициализация фигуры Plotly для отображения данных
    fig = go.Figure()
    # Добавление гистограммы для объемов Bid с настройками визуализации
    fig.add_trace(go.Bar(
        x=bid_data['total_quantity'], y=bid_data['price_level'], name='Bid', orientation='h',
        marker=dict(color='green'), text=bid_data['total_quantity'].round(), textposition='outside',
        textfont=dict(size=14), hoverinfo='none', hovertemplate='Объем: %{x:.0f} BTC<br>' + 'Цена: %{y:.0f}$<br>'))

    # Добавление гистограммы для объемов Ask с настройками визуализации
    fig.add_trace(go.Bar(
        x=ask_data['total_quantity'], y=ask_data['price_level'], name='Ask', orientation='h',
        marker=dict(color='red'), text=ask_data['total_quantity'].round(), textposition='outside',
        textfont=dict(size=14), hoverinfo='none', hovertemplate='Объем: %{x:.0f} BTC<br>' + 'Цена: %{y:.0f}$<br>'))

    # Расчет дополнительного диапазона для оси X для лучшей визуализации
    range_extension = (float(dist['total_quantity'].max()) - float(dist['total_quantity'].min())) * 0.1
    # Обновление настроек макета графика
    fig.update_layout(
        margin=dict(l=0, t=0, b=0, r=0), showlegend=False, template='plotly_dark',
        xaxis=dict(range=[float(dist['total_quantity'].min()), float(dist['total_quantity'].max()) + range_extension])
    )

    return fig


@app.callback(
    Output("trades-graph", "figure"),
    [Input('interval-component', 'n_intervals'),
     Input('graph-selector', 'value')],
    [State("slider-days-trades", "value"),
     State("type-data-trades", "value")]
)
def update_graph_trades(n_interval, selector_value, n_days, data_type):
    # Построение графика соотношения покупок к продажам
    if selector_value == 'ratio':
        # Получение данных метрики
        ratio = bc.get_trades_metrics(data_type, selector_value)

        # Создание фигуры с двумя осями Y для разных масштабов данных
        fig = make_subplots(specs=[[{"secondary_y": True}]])

        # Расчет среднего значения соотношения покупок к продажам за предыдущие 7 дней
        mean_ratio = ratio['buy_sell_ratio'].iloc[:-1].mean()

        # Ограничение данных выбранным количеством дней
        ratio = ratio.tail(n_days)

        # Добавление графиков на фигуру: среднее значение, столбцы покупок и продаж, линия соотношения
        fig.add_trace(
            go.Scatter(
                x=ratio['trade_date'],
                y=[mean_ratio] * len(ratio),
                mode='lines',
                name='Average',
                line=dict(color='gray', dash='dash'),
                hoverinfo='none', hovertemplate='buySellRatio: %{y:.2f}<br>'
            ), secondary_y=True
        )

        fig.add_trace(go.Bar(
            x=ratio['trade_date'],
            y=ratio['percentage_buy'],
            name='BUY',
            marker_color='green',
            hoverinfo="none"
        ), secondary_y=False)

        fig.add_trace(go.Bar(
            x=ratio['trade_date'],
            y=ratio['percentage_sell'],
            name='SELL',
            marker_color='red',
            base=ratio['percentage_buy'],  # Это позволяет наложить SELL на BUY
            hoverinfo="none"
        ), secondary_y=False)

        fig.add_trace(go.Scatter(
            x=ratio['trade_date'],
            y=ratio['buy_sell_ratio'],
            text=[
                f'Коэффициент: {ratio:.2f}<br>BUY: {buy:.2f}%<br>SELL: {sell:.2f}%'
                for ratio, buy, sell in zip(ratio['buy_sell_ratio'], ratio['percentage_buy'],
                                            ratio['percentage_sell'])
            ],
            hoverinfo='text',
            name='Ratio',
            mode='lines+markers',
            line=dict(color='black'),
            marker=dict(color='white', size=10, line=dict(width=2, color='darkblue'))
        ), secondary_y=True)

        fig.add_annotation(
            x=ratio['trade_date'].iloc[-1],
            y=ratio['buy_sell_ratio'].iloc[-1],
            text=f"{ratio['buy_sell_ratio'].iloc[-1]:.2f}",
            showarrow=False,
            font=dict(
                family="Courier New, monospace",
                size=15,
                color="#ffffff"
            ),
            yref='y2',
            yshift=40 if ratio['buy_sell_ratio'].iloc[-1] >= 1 else -40,
            align='center',
            bordercolor="#c7c7c7",
            borderwidth=2,
            borderpad=5,
            bgcolor="#008000" if ratio['buy_sell_ratio'].iloc[-1] >= 1 else "#FF0000",
        )

        # Настройка внешнего вида и параметров графика
        fig.update_layout(
            template='plotly_dark',
            barmode='overlay',  # Наложение столбцов друг на друга
            yaxis=dict(fixedrange=True, tickvals=[0, 50, 100], ticktext=['0%', '50%', '100%']),
            yaxis2=dict(
                fixedrange=True,
                overlaying='y',
                side='right',
                range=[float(ratio['buy_sell_ratio'].min()) - 0.2,
                       float(ratio['buy_sell_ratio'].max()) + 0.2],
                # Более полный набор меток для оси Y2
                showgrid=False,
            ),
            showlegend=False,
            margin=dict(l=0, t=0, b=0, r=0)
        )

        return fig

    # Построение графика дельты между покупками и продажами
    elif selector_value == 'delta':
        # Получение данных метрики
        delta = bc.get_trades_metrics(data_type, selector_value)

        # Расчет среднего значения соотношения покупок к продажам за предыдущие 7 дней
        mean_delta = delta['delta'].iloc[:-1].mean()

        # Ограничение данных выбранным количеством дней
        delta = delta.tail(n_days)

        # Определение цвета столбцов в зависимости от значения дельты
        colors = ['green' if val > 0 else 'red' for val in delta['delta'].round()]

        # Создание и настройка барного графика
        fig = go.Figure(data=[
            go.Bar(
                x=delta['trade_date'],
                y=delta['delta'],
                marker_color=colors,
                name='Delta',
                text=[f"{val:.0f}" for val in delta['delta']],
                textposition='outside', textfont=dict(size=14),
                hoverinfo='none',
                hovertemplate='Дата: %{x}<br>' + 'Дельта: %{y:.0f}<extra></extra>'
            )
        ])

        fig.add_trace(go.Scatter(
            x=delta['trade_date'],
            y=[mean_delta] * len(delta),
            mode='lines',
            name='Average 7D',
            line=dict(dash='dash', color='gray', width=2),
            hoverinfo='none', hovertemplate='Delta: %{y:.2f}<br>'
        ))

        range_extension = (float(delta['delta'].max()) - float(delta['delta'].min())) * 0.3
        fig.update_layout(
            showlegend=False,
            template='plotly_dark',
            yaxis=dict(
                range=[float(delta['delta'].min()) - range_extension, float(delta['delta'].max()) + range_extension],
                fixedrange=True,
                showgrid=False
            ),
            xaxis=dict(
                fixedrange=True
            ),
            margin=dict(l=0, t=0, b=0, r=0)
        )

        return fig

    # Построение графика распределения объемов торгов по ценам
    else:
        # Получение данных метрики
        dist = bc.get_trades_metrics(data_type, selector_value, n_days)

        # Текущая цена
        price = float(bc.current_price()['price'].iloc[0])

        # Определяем цвета на основе текущей цены
        dist['color'] = dist['price_round'].apply(lambda x: 'green' if x < price else 'red')

        # Создание и настройка барного графика
        fig = go.Figure(go.Bar(
            x=dist['volume'],
            y=dist['price_round'],
            name='Distribution',
            orientation='h',
            marker_color=dist['color'],
            text=[f"{val / 1000:.0f}K" for val in dist['volume']],
            textposition='outside',
            textfont=dict(size=14),
            hoverinfo='none',
            hovertemplate='Цена: %{y}<br>' + 'Объем: %{x:.0f}<br>'
        ))

        range_extension = (float(dist['volume'].max()) - float(dist['volume'].min())) * 0.3
        fig.update_layout(
            margin=dict(l=0, r=0, t=0, b=0),
            template='plotly_dark',
            showlegend=False,
            xaxis=dict(
                range=[
                    float(dist['volume'].min()), float(dist['volume'].max()) + range_extension
                ],
            )
        )

        return fig


@app.callback(
    Output('analysis-graph', 'figure'),
    [Input('interval-component', 'n_intervals'),
     Input('graph-selector-analysis', 'value')],
    [State("slider-days-analysis", "value"),
     State("type-data-analysis", "value")]
)
def update_graph_analysis(n_interval, selector_value, days, data_type):
    # Анализ изменения котировок за определенный период (волатильности)
    if selector_value == 'kline':
        # Получение данных котировок
        kline = bc.get_kline('BTCUSDT', '1d', days, 'Binance Futures', 'dashboard')

        # Расчет среднего и стандартного отклонения процентного изменения цены
        mean = kline['pct_change'].mean()
        std_dev = kline['pct_change'].std()

        # Создание и настройка графика
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=kline.index,
            y=kline['pct_change'],
            mode='lines+markers',
            name='% Change Price',
            line=dict(color='gray'),
            marker=dict(color='white', size=8, line=dict(color='blue', width=2)),
            hoverinfo='none',
            hovertemplate='Дата: %{x}<br>' + 'Значение: %{y:.2f}%<br>'
        ))

        fig.add_annotation(
            x=kline.index[-1],
            y=kline['pct_change'].iloc[-1],
            text=f"+{kline['pct_change'].iloc[-1]:.2f}%" if kline['pct_change'].iloc[
                                                                -1] >= 0 else f"{kline['pct_change'].iloc[-1]:.2f}%",
            showarrow=False,
            font=dict(
                family="Courier New, monospace",
                size=15,
                color="#ffffff"
            ),
            yshift=40 if kline['pct_change'].iloc[-1] >= 0 else -40,
            align='center',
            bordercolor="#c7c7c7",
            borderwidth=2,
            borderpad=5,
            bgcolor="#008000" if kline['pct_change'].iloc[-1] >= 0 else "#FF0000",
        )

        # Линия для среднего + стандартное отклонение
        fig.add_hline(y=mean + std_dev, line=dict(color='red', width=2, dash='dash'), name='Mean + STD',
                      layer='below')

        # Линия для среднего - стандартное отклонение
        fig.add_hline(y=mean - std_dev, line=dict(color='green', width=2, dash='dash'), name='Mean - STD',
                      layer='below')

        fig.add_annotation(
            xref='paper', x=1, xanchor='right', y=mean + std_dev + 0.5,
            text=f"std",
            showarrow=False, font=dict(size=12, color='red'), align='right')

        fig.add_annotation(
            xref='paper', x=1, xanchor='right', y=mean - std_dev + 0.5,
            text=f"std",
            showarrow=False, font=dict(size=12, color='green'), align='right')

        fig.update_layout(
            margin=dict(l=0, t=0, b=0, r=0), showlegend=False, template='plotly_dark', xaxis=dict(showgrid=False),
            yaxis=dict(range=[float(kline['pct_change'].min()) - 5, float(kline['pct_change'].max()) + 5])
        )

        return fig

    # Анализ соотношения длинных и коротких позиций
    elif selector_value == 'longShortRatio':
        # Получение данных
        ratio = bc.get_ratio(data_type)

        # Создание фигуры с двумя осями Y
        fig = make_subplots(specs=[[{"secondary_y": True}]])

        # Среднее значение за последние 7 дней
        mean_ratio = ratio['longShortRatio'].iloc[:-1].mean()

        # Ограничение данных выбранным количеством дней
        ratio = ratio.tail(days).reset_index()
        ratio['longAccount'] = ratio['longAccount'].mul(100)
        ratio['shortAccount'] = ratio['shortAccount'].mul(100)

        # Добавление линии со средним значением
        fig.add_trace(
            go.Scatter(
                x=ratio['timestamp'],
                y=[mean_ratio] * len(ratio),
                mode='lines',
                name='Average 7D',
                line=dict(color='gray', dash='dash'),
                hoverinfo='none', hovertemplate='longShortRatio: %{y:.2f}<br>'
            ), secondary_y=True
        )

        # Long
        fig.add_trace(go.Bar(
            x=ratio['timestamp'],
            y=ratio['longAccount'],
            name='Long',
            marker_color='green',
            hoverinfo='none'
        ), secondary_y=False)

        # Short
        fig.add_trace(go.Bar(
            x=ratio['timestamp'],
            y=ratio['shortAccount'],
            name='Short',
            marker_color='red',
            base=ratio['longAccount'],
            hoverinfo='none'
        ), secondary_y=False)

        # Добавляем линию коэффициента соотношения
        fig.add_trace(go.Scatter(
            x=ratio['timestamp'],
            y=ratio['longShortRatio'],
            name='longShortRatio',
            mode='lines+markers',
            line=dict(color='black'),
            marker=dict(color='white', size=10, line=dict(width=2, color='darkblue')),
            text=[
                f'Коэффициент: {ratio:.2f}<br>Long: {buy:.2f}%<br>Short: {sell:.2f}%'
                for ratio, buy, sell in zip(ratio['longShortRatio'], ratio['longAccount'],
                                            ratio['shortAccount'])
            ],
            hoverinfo='text',
        ), secondary_y=True)

        fig.add_annotation(
            x=ratio['timestamp'].iloc[-1],
            y=ratio['longShortRatio'].iloc[-1],
            showarrow=False,
            text=f"{ratio['longShortRatio'].iloc[-1]:.2f}",
            font=dict(
                family="Courier New, monospace",
                size=15,
                color="#ffffff"
            ),
            yref='y2',
            yshift=40 if ratio['longShortRatio'].iloc[-1] >= 1 else -40,
            align='center',
            bordercolor="#c7c7c7",
            borderwidth=2,
            borderpad=5,
            bgcolor="#008000" if ratio['longShortRatio'].iloc[-1] >= 1 else "#FF0000",
        )

        # Настройки графика
        fig.update_layout(
            barmode='overlay',
            yaxis=dict(fixedrange=True, tickvals=[0, 50, 100], ticktext=['0%', '50%', '100%']),
            yaxis2=dict(
                fixedrange=True,
                overlaying='y',
                side='right',
                range=[float(ratio['longShortRatio'].min()) - 0.5,
                       float(ratio['longShortRatio'].max()) + 0.5],
                showgrid=False,
            ),
            showlegend=False,
            margin=dict(l=0, t=0, b=0, r=0),
            template='plotly_dark'
        )

        return fig

    # Анализ данных по ликвидациям
    elif selector_value == 'liquidationRate':
        # Получение данных
        ratio = bc.get_liquidation_metrics(days, 'ratio')

        # Создание фигуры с двумя осями Y
        fig = make_subplots(specs=[[{"secondary_y": True}]])

        # Среднее значение за последние 7 дней
        mean_ratio = ratio['ratio'].iloc[:-1].mean()

        # Фильтр данных по дням
        ratio = ratio.tail(days).reset_index()

        # Добавляем линию со средним значением
        fig.add_trace(
            go.Scatter(
                x=ratio['trade_date'],
                y=[mean_ratio] * len(ratio),
                mode='lines',
                name='Average 7D',
                line=dict(color='gray', dash='dash'),
                hoverinfo='none', hovertemplate='liquidationRatio: %{y:.2f}<br>'
            ), secondary_y=True
        )

        # Добавляем бары ликвидации покупок
        fig.add_trace(go.Bar(
            x=ratio['trade_date'],
            y=ratio['BUY_liq'],
            name='buyLiquidation',
            marker_color='green',
            hoverinfo='none'
        ), secondary_y=False)

        # Добавляем бары ликвидации продаж
        fig.add_trace(go.Bar(
            x=ratio['trade_date'],
            y=ratio['SELL_liq'],
            name='sellLiquidation',
            marker_color='red',
            hoverinfo='none',
            base=ratio['BUY_liq']
        ), secondary_y=False)

        # Добавляем линию коэффициента соотношения
        fig.add_trace(go.Scatter(
            x=ratio['trade_date'],
            y=ratio['ratio'],
            name='liquidationRatio',
            mode='lines+markers',
            line=dict(color='gray'),
            marker=dict(color='white', size=10, line=dict(width=2, color='darkblue')),
            text=[
                f'Коэффициент: {ratio:.2f}<br>Long: {buy:.2f} BTC<br>Short: {sell:.2f} BTC<br>Дата: {date}'
                for ratio, buy, sell, date in zip(ratio['ratio'], ratio['BUY_liq'],
                                                  ratio['SELL_liq'], ratio['trade_date'])
            ],
            hoverinfo='text'
        ), secondary_y=True)

        # Добавляем аннотацию
        fig.add_annotation(
            x=ratio['trade_date'].iloc[-1],
            y=ratio['ratio'].iloc[-1],
            showarrow=False,
            text=f"{ratio['ratio'].iloc[-1]:.2f}",
            font=dict(
                family="Courier New, monospace",
                size=15,
                color="#ffffff"
            ),
            yref='y2',
            yshift=40 if ratio['ratio'].iloc[-1] >= 1 else -40,
            align='center',
            bordercolor="#c7c7c7",
            borderwidth=2,
            borderpad=5,
            bgcolor="#008000" if ratio['ratio'].iloc[-1] >= 1 else "#FF0000",
        )

        # Настройки внешнего вида графика
        fig.update_layout(
            barmode='overlay',  # Наложение столбцов друг на друга
            yaxis=dict(
                fixedrange=True, range=[0, ratio['BUY_liq'].max() + ratio['SELL_liq'].max() + 100]
            ),
            yaxis2=dict(
                fixedrange=True,
                overlaying='y',
                side='right',
                range=[float(ratio['ratio'].min()) - 0.5,
                       float(ratio['ratio'].max()) + 0.5],
                showgrid=False,
            ),
            showlegend=False,
            margin=dict(l=0, t=0, b=0, r=0),
            template='plotly_dark'
        )

        return fig


@app.callback(
    Output('analysis-graph-2', 'figure'),
    [Input('interval-component', 'n_intervals'),
     Input('graph-selector-analysis-2', 'value')],
    [State("slider-days-analysis-2", "value")]
)
def update_graph_analysis_2(n_interval, selector_value, days):
    # анализ финансирования
    if selector_value == 'funding':
        funding = bc.get_funding()

        # Среднее значение
        mean_funding = funding['fundingRate'].iloc[:-1].mean()

        # Фильтр данных по дням
        funding = funding.tail(days * 3).reset_index()

        # Создание столбца с цветами для каждого значения
        funding['color'] = funding['fundingRate'].apply(lambda x: 'green' if x > 0 else 'red')

        # Создание фигуры с поддержкой второй оси Y
        fig = make_subplots(specs=[[{"secondary_y": True}]])

        # Добавляем линию со средним значением
        fig.add_trace(
            go.Scatter(
                x=funding['fundingTime'],
                y=[mean_funding] * len(funding),
                mode='lines',
                name='Average 7D',
                line=dict(color='gray', dash='dash'),
                hoverinfo='none', hovertemplate='Funding Rate: %{y:.4f}%<br>'
            )
        )

        # Добавление баров на график для значений
        fig.add_trace(
            go.Bar(x=funding['fundingTime'], y=funding['fundingRate'], name='Funding Rate',
                   marker_color=funding['color'],
                   hoverinfo='none', hovertemplate='Дата: %{x}<br>' + 'Ставка: %{y:.4f}%<br>'),
            secondary_y=False)

        # Добавление линейного графика для цен
        fig.add_trace(
            go.Scatter(x=funding['fundingTime'], y=funding['markPrice'], name='Mark Price', mode='lines',
                       line=dict(color='gray'), hoverinfo='none',
                       hovertemplate='Дата: %{x}<br>' + 'Цена: %{y:.0f}$<br>'),
            secondary_y=True)

        fig.add_annotation(
            x=funding['fundingTime'].iloc[-1],
            y=funding['fundingRate'].iloc[-1],
            text=f"{funding['fundingRate'].iloc[-1]:.4f}%",
            showarrow=False,
            font=dict(
                family="Courier New, monospace",
                size=15,
                color="#ffffff"
            ),
            yshift=40 if funding['fundingRate'].iloc[-1] >= 0 else -40,
            align='center',
            bordercolor="#c7c7c7",
            borderwidth=2,
            borderpad=5,
            bgcolor="#008000" if funding['fundingRate'].iloc[-1] >= 0 else "#FF0000",
        )

        # Обновление макета для улучшения визуализации
        fig.update_layout(
            yaxis=dict(fixedrange=True, showgrid=False,
                       range=[0, funding['fundingRate'].max() + 0.015]),
            yaxis2=dict(fixedrange=True, showgrid=False,
                        range=[funding['markPrice'].min(), funding['markPrice'].max() + 1000]),
            margin=dict(l=0, t=0, b=0, r=0), showlegend=False, template='plotly_dark'
        )

        return fig

    # анализ открытого интереса
    elif selector_value == 'oi':
        kline = bc.get_kline('BTCUSDT', '1d', days, 'Binance Futures', 'dashboard')
        oi = bc.get_oi()

        # Среднее значение за последние 7 дней
        mean_oi = oi['sumOpenInterest'].iloc[:-1].mean()

        # Фильтр данных по дням
        oi = oi.tail(days).reset_index()

        # Создаем список для цветов баров
        bar_colors = ['green' if oi['sumOpenInterest'][i] > oi['sumOpenInterest'][i - 1] else 'red'
                      for i in range(1, days)]

        # Цвет для первого элемента
        bar_colors.insert(0, 'green')

        fig = make_subplots(specs=[[{"secondary_y": True}]])

        # Добавляем линию со средним значением
        fig.add_trace(
            go.Scatter(
                x=oi['timestamp'],
                y=[mean_oi] * len(oi),
                mode='lines',
                name='Average 7D',
                line=dict(color='gray', dash='dash'),
                hoverinfo='none', hovertemplate='OI: %{y:.0f} BTC<br>'
            )
        )

        # Создаем барный график
        fig.add_trace(
            go.Bar(
                x=oi['timestamp'],
                y=oi['sumOpenInterest'],
                marker_color=bar_colors,
                name='OpenInterest',
                hoverinfo='none',
                hovertemplate='Дата: %{x}<br>' + 'OI: %{y:.0f} BTC<br>'
            )
        )

        fig.add_trace(
            go.Scatter(x=kline.index, y=kline['close'], name='Mark Price', mode='lines', line=dict(color='gray'),
                       hoverinfo='none', hovertemplate='Дата: %{x}<br>' + 'Цена: %{y:.0f}$<br>'), secondary_y=True)

        fig.add_annotation(
            x=oi['timestamp'].iloc[-1],
            y=oi['sumOpenInterest'].iloc[-1],
            text=f"{oi['sumOpenInterest'].iloc[-1] / 1000:.1f}K BTC",
            showarrow=False,
            font=dict(
                family="Courier New, monospace",
                size=15,
                color="#ffffff"
            ),
            yshift=40,
            align='center',
            bordercolor="#c7c7c7",
            borderwidth=2,
            borderpad=5,
            bgcolor="#008000"
        )

        gap = oi['sumOpenInterest'].max() * 0.3
        fig.update_layout(yaxis=dict(fixedrange=True, showgrid=False, range=[0, oi['sumOpenInterest'].max() + gap]),
                          yaxis2=dict(fixedrange=True, showgrid=False,
                                      range=[kline['close'].min(), kline['close'].max() + 1000]),
                          margin=dict(l=0, t=0, b=0, r=0), showlegend=False, template='plotly_dark')

        return fig

    # анализ ликвидаций
    elif selector_value == 'liquidationByPrice':
        dist = bc.get_liquidation_metrics(days, 'dist')

        # Текущая цена
        price = float(bc.current_price()['price'].iloc[0])

        # Определяем цвета на основе текущей цены
        dist['color'] = dist['price_round'].apply(lambda x: 'green' if x < price else 'red')

        # Создаем фигуру
        fig = go.Figure(go.Bar(
            x=dist['volume'],
            y=dist['price_round'],
            orientation='h',
            marker_color=dist['color'],
            name='Liquidation',
            hoverinfo='none',
            hovertemplate='Цена: %{y}<br>' + 'Объем BTC: %{x:.2f}<br>'
        ))

        # Добавляем аннотацию
        mask = dist['volume'] == dist['volume'].max()
        fig.add_annotation(
            x=dist['volume'].max(),
            y=dist.loc[mask, 'price_round'].iloc[0],
            showarrow=False,
            text=f"{dist['volume'].max():.2f} BTC",
            font=dict(
                family="Courier New, monospace",
                size=15,
                color="#ffffff"
            ),
            xshift=60,
            align='center',
            bordercolor="#c7c7c7",
            borderwidth=2,
            borderpad=5,
            bgcolor="#008000"
        )

        # Обновляем настройки графика
        range_extension = (float(dist['volume'].max()) - float(dist['volume'].min())) * 0.3
        fig.update_layout(
            margin=dict(l=0, r=0, t=0, b=0),
            showlegend=False,
            xaxis=dict(
                range=[
                    float(dist['volume'].min()), float(dist['volume'].max()) + range_extension
                ],
            ),
            template='plotly_dark'
        )

        return fig


# === layout_terminal === #
# Функции обратного вызова для управления отображением модального окна в терминале
@app.callback(
    Output("offCanvas", "is_open"),
    [Input("setup-terminal", "n_clicks"),
     Input("apply-filters-candle", "n_clicks")],
    [State("offCanvas", "is_open")],
)
def toggle_offCanvas(n_open, n_apply, is_open):
    if n_open or n_apply:
        return not is_open
    return is_open


@app.callback(
    Output("modal-cluster_search", "is_open"),
    [Input("cluster-search", "n_clicks"),
     Input("apply-cluster-search", "n_clicks")],
    [State("modal-cluster_search", "is_open")],
)
def toggle_cluster_search(n_open, n_apply, is_open):
    if n_open or n_apply:
        return not is_open
    return is_open


# Функции обратного вызова для регулярного обновления метрик терминала
@app.callback(
    Output('price-value', 'children'),
    [Input('interval-component-2', 'n_intervals')]
)
def update_metrics_candle(n):
    price = bc.current_price()['price'].astype(float).iloc[0]

    return f"${price:.2f}"


# Функции обратного вызова для динамического обновления графика в терминале
@app.callback(
    Output("candle-graph", "figure"),
    [Input('interval-component-2', 'n_intervals'),
     Input("symbol-dropdown", "value"),
     Input("source-dropdown", "value"),
     Input("timeframe-slider", "value"),
     Input("amount-days-slider", "value"),
     Input("type-dropdown", "value"),
     Input("filter-slider-cluster", "value"),
     Input("indicator-dropdown", "value")],
)
def update_graph_candle(n, symbol_, exchange_name, timeframe, days, anomalies_type, anomalies_filter, indicators):
    # Декодер для timeframe
    timeframe_decode = {
        0: '1h',
        1: '2h',
        2: '4h',
        3: '1d'
    }
    timeframe = timeframe_decode[timeframe]

    # Функция для получения данных с биржи
    kline = bc.get_kline(symbol_, timeframe, days, exchange_name, 'terminal')

    # проверка статуса на наличие индикатора
    if len(indicators) > 0:
        row = 1

        # Создание макета
        if 'Cumulative Delta' in indicators and len(indicators) == 1:
            fig = make_subplots(
                rows=1, cols=1,
                shared_xaxes=True,
                specs=[[{"secondary_y": True}]]
            )
        elif 'Cumulative Delta' in indicators and len(indicators) == 2:
            fig = make_subplots(
                rows=2, cols=1,
                shared_xaxes=True,
                specs=[[{"secondary_y": True}], [{'secondary_y': False}]],
                row_heights=[0.7, 0.3],
                vertical_spacing=0.01
            )
        elif 'Cumulative Delta' in indicators and len(indicators) == 3:
            fig = make_subplots(
                rows=3, cols=1,
                shared_xaxes=True,
                specs=[[{"secondary_y": True}], [{'secondary_y': False}], [{'secondary_y': False}]],
                row_heights=[0.6, 0.2, 0.2],
                vertical_spacing=0.01
            )
        else:
            fig = make_subplots(
                rows=len(indicators) + 1, cols=1,
                shared_xaxes=True,
                vertical_spacing=0.01,
                row_heights=[0.7, 0.3] if len(indicators) == 1 else [0.6, 0.2, 0.2]
            )

        # Добавление свечного графика
        fig.add_trace(
            go.Candlestick(
                x=kline.index,
                open=kline['open'],
                high=kline['high'],
                low=kline['low'],
                close=kline['close'],
                name='Candle'
            ),
            row=row, col=1)
        row += 1

        if 'Cumulative Delta' in indicators:
            # Добавление графика Кумулятивная дельта
            row -= 1
            fig.add_trace(
                go.Scatter(
                    x=kline.index, y=kline['cumulative_delta'],
                    mode='lines', name='cumDelta', line=dict(color='gray', width=1),
                    hoverinfo='none',
                    hovertemplate='Дата: %{x}<br>' + 'Значение: %{y:.0f}<br>'
                ),
                row=row, col=1, secondary_y=True)

            fig.update_yaxes(secondary_y=True, side='left', showgrid=False)
            row += 1
        if 'Volume' in indicators:
            # Добавление графика объема
            fig.add_trace(
                go.Bar(x=kline.index, y=kline['volume'], name='Volume', marker=dict(color='gray'),
                       hoverinfo='none',
                       hovertemplate='Дата: %{x}<br>' + 'Значение: %{y:.0f}<br>'
                       ),
                row=row, col=1)
            row += 1

            slider = False
        if 'Delta' in indicators:
            # Добавление графика дельта
            fig.add_trace(
                go.Bar(x=kline.index, y=kline['delta'], name='Delta',
                       marker=dict(color=['green' if x > 0 else 'red' for x in kline['delta']]),
                       hoverinfo='none',
                       hovertemplate='Дата: %{x}<br>' + 'Значение: %{y:.0f}<br>'
                       ),
                row=row, col=1)
            row += 1
            slider = False

    else:
        fig = go.Figure(
            go.Candlestick(
                x=kline.index,
                open=kline['open'],
                high=kline['high'],
                low=kline['low'],
                close=kline['close'],
                name='Candle'
            )
        )

    # проверка статуса на инициализацию поиска аномалий
    if anomalies_type is not None:
        start_date = datetime.now() - timedelta(days=days)
        if anomalies_type.split()[-1] == '(candle)':
            highlight = bc.cluster_search(
                anomalies_type, anomalies_filter, timeframe, symbol_, exchange_name, start_date, kline
            )

            # Создание дополнительного графика свечей для выделения аномалий
            fig.add_trace(
                go.Candlestick(
                    x=highlight,
                    open=kline['open'][highlight],
                    high=kline['high'][highlight],
                    low=kline['low'][highlight],
                    close=kline['close'][highlight],
                    increasing=dict(line=dict(color='orange')),
                    decreasing=dict(line=dict(color='orange')),
                    name=anomalies_type
                )
            )
        else:
            specific_time, price_level = bc.cluster_search(
                anomalies_type, anomalies_filter, timeframe, symbol_, exchange_name, start_date
            )

            fig.add_trace(go.Scatter(x=specific_time, y=price_level,
                                     mode='markers', marker=dict(size=15, color='orange'),
                                     name=anomalies_type,
                                     hoverinfo='none',
                                     hovertemplate='Дата: %{x}<br>' + 'Цена: %{y:.0f}$<br>'))

            # Добавление горизонтальных линий для каждого ценового уровня
            for price in price_level:
                fig.add_shape(type='line',
                              x0=kline.index[0], y0=price, x1=kline.index[-1], y1=price,
                              line=dict(color='green' if kline['close'].iloc[-1] > price else 'red', width=0.5,
                                        dash='dash'))

    # Настройка макета
    max_value = max(kline['high'])
    min_value = min(kline['low'])
    fig.update_layout(
        yaxis=dict(
            side='right',
            range=[min_value, max_value + 1000]
        ),
        xaxis_rangeslider_visible=False,
        showlegend=False,
        margin=dict(l=0, r=0, t=0, b=0),
        template='plotly_dark'
    )

    return fig


if __name__ == '__main__':
    # Конфигурация логирования
    logging.basicConfig(
        level=logging.WARNING,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # Запуск приложения
    app.run_server(debug=False, host='0.0.0.0', port='8050')
