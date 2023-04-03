from vnpy_ctastrategy import (
    CtaTemplate,
    StopOrder,
    TickData,
    BarData,
    TradeData,
    OrderData,
    BarGenerator,
    ArrayManager,
)

from vnpy.trader.constant import Interval

class VegasStrategy(CtaTemplate):
    """"""

    author = "myron"

    fast_window = 12
    ema_144_window = 144
    ema_169_window = 169
    ema_576_window = 288
    ema_676_window = 388
    disable_long_trace = True
    fixed_size = 1

    fast_ma = 0
    ema_144 = 0
    ema_169 = 0
    ema_576 = 0
    ema_676 = 0
    fast_ma_lag = 0
    ema_144_lag = 0
    ema_169_lag = 0
    ema_576_lag = 0
    ema_676_lag = 0

    parameters = [
        "fast_window",
        "ema_144_window",
        "ema_169_window",
        "ema_576_window",
        "ema_676_window",
        "disable_long_trace",
        "fixed_size"
    ]
    variables = [
        "fast_ma",
        "ema_144",
        "ema_169",
        "ema_576",
        "ema_676",
        "fast_ma_lag",
        "ema_144_lag",
        "ema_169_lag",
        "ema_576_lag",
        "ema_676_lag"
    ]

    def __init__(self, cta_engine, strategy_name, vt_symbol, setting):
        """"""
        super().__init__(cta_engine, strategy_name, vt_symbol, setting)

        self.bg = BarGenerator(
            on_bar=self.on_bar,
            window=4,
            on_window_bar=self.on_4hour_bar,
            interval = Interval.HOUR
        )
        if self.disable_long_trace:
            self.am = ArrayManager(self.ema_169_window)
        else:
            self.am = ArrayManager(self.ema_676_window)

    def on_init(self):
        """
        Callback when strategy is inited.
        """
        self.write_log("策略初始化")

        if self.disable_long_trace:
            self.load_bar(100)
        else:
            self.load_bar(140)

    def on_start(self):
        """
        Callback when strategy is started.
        """
        self.write_log("策略启动")

    def on_stop(self):
        """
        Callback when strategy is stopped.
        """
        self.write_log("策略停止")

    def on_tick(self, tick: TickData):
        """
        Callback of new tick data update.
        """
        self.bg.update_tick(tick)

    def on_bar(self, bar: BarData):
        """
        Callback of new bar data update.
        """
        self.bg.update_bar(bar)

    def on_4hour_bar(self, bar: BarData):
        """
        Callback of new 15-minute bar data update.
        """
        self.am.update_bar(bar)
        if not self.am.inited:
            return

        self.fast_ma_lag, self.fast_ma = self.am.ema(self.fast_window, array=True)[-2:]
        self.ema_144_lag, self.ema_144 = self.am.ema(self.ema_144_window, array=True)[-2:]
        self.ema_169_lag, self.ema_169 = self.am.ema(self.ema_169_window, array=True)[-2:]
        try:
            self.ema_576_lag, self.ema_576 = self.am.ema(self.ema_576_window, array=True)[-2:]
            self.ema_676_lag, self.ema_676 = self.am.ema(self.ema_676_window, array=True)[-2:]
        except:
            self.disable_long_trace = True

        self.write_trace("Vegas计算: fast_ma_lag: {}, ema_144_lag: {}, fast_ma: {}, ema_144: {}, ema_169: {}, disable_long_trace: {}, ema_576: {}, ema_676: {}".format(
            self.fast_ma_lag,
            self.ema_144_lag,
            self.fast_ma,
            self.ema_144,
            self.ema_169,
            self.disable_long_trace,
            self.ema_576,
            self.ema_676
        ))
        if(self.fast_ma_lag < self.ema_144_lag
        and self.fast_ma > self.ema_144
        and self.ema_144 > self.ema_169
        and (self.disable_long_trace or self.ema_576 > self.ema_676)):
            self.buy(bar.close_price, self.fixed_size)
            self.cta_engine.put_strategy_action_event(self, "buy", bar.datetime)
            self.put_event()