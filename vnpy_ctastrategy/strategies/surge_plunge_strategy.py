from vnpy_ctastrategy import (
    StopOrder,
    TickData,
    BarData,
    TradeData,
    OrderData,
    BarGenerator,
    ArrayManager,
    CtaSignal,
    CtaTemplate
)


class SurgePlungeSignal(CtaSignal):
    """"""

    def __init__(self, bar_window: int, surge_ratio: float, plunge_ratio: float):
        """Constructor"""
        super().__init__()

        self.bg = BarGenerator(
            self.on_bar,
            window=bar_window,
            on_window_bar=self.on_window_bar)
        self.surge_ratio = surge_ratio
        self.plunge_ratio = plunge_ratio
        self.open_price = 0
        self.close_price = 0

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

    def on_window_bar(self, bar: BarData):
        if bar.close_price >= bar.open_price * (1 + self.surge_ratio):
            self.set_signal_pos(1)
        elif bar.close_price <= bar.open_price * (1 - self.plunge_ratio):
            self.set_signal_pos(-1)
        else:
            self.set_signal_pos(0)
        self.open_price = bar.open_price
        self.close_price = bar.close_price

class SurgePlungeStrategy(CtaTemplate):
    """"""

    author = "myron"

    quick_window = 5
    quick_surge_ratio = 0.03
    quick_plunge_ratio = 0.03

    medium_window = 15
    medium_surge_ratio = 0.05
    medium_plunge_ratio = 0.05

    slow_window = 30
    slow_surge_ratio = 0.10
    slow_plunge_ratio = 0.10


    signal_pos = {}
    target_pos = 1

    parameters = ["quick_window", "quick_surge_ratio", "quick_plunge_ratio",
                  "medium_window", "medium_surge_ratio", "medium_plunge_ratio",
                  "slow_window", "slow_surge_ratio", "slow_plunge_ratio"]
    variables = ["signal_pos", "target_pos"]

    def __init__(self, cta_engine, strategy_name, vt_symbol, setting):
        """"""
        super().__init__(cta_engine, strategy_name, vt_symbol, setting)

        self.quick_signal = SurgePlungeSignal(self.quick_window, self.quick_surge_ratio, self.quick_plunge_ratio)
        self.medium_signal = SurgePlungeSignal(self.medium_window, self.medium_surge_ratio, self.medium_plunge_ratio)
        self.slow_signal = SurgePlungeSignal(self.slow_window, self.slow_surge_ratio, self.slow_plunge_ratio)

        self.signal_pos = {
            "quick": 0,
            "medium": 0,
            "slow": 0
        }

    def on_init(self):
        """
        Callback when strategy is inited.
        """
        self.write_log("策略初始化")

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

        self.quick_signal.on_tick(tick)
        self.medium_signal.on_tick(tick)
        self.slow_signal.on_tick(tick)

        self.calculate_target_pos(tick.datetime)

    def on_bar(self, bar: BarData):
        """
        Callback of new bar data update.
        """

        self.quick_signal.on_bar(bar)
        self.medium_signal.on_bar(bar)
        self.slow_signal.on_bar(bar)

        self.calculate_target_pos(bar.datetime)

    def calculate_target_pos(self, datetime):
        """"""
        self.signal_pos["quick"] = self.quick_signal.get_signal_pos()
        self.signal_pos["medium"] = self.medium_signal.get_signal_pos()
        self.signal_pos["slow"] = self.slow_signal.get_signal_pos()

        current_pos = 0
        for v in self.signal_pos.values():
            current_pos += v

        if current_pos >= self.target_pos:
            self.write_trace("Signal计算: quick: {}, medium: {}, slow: {}, quick_open_price: {}, quick_close_price: {}, medium_open_price: {}, medium_close_price: {}, slow_open_price: {}, slow_close_price: {}, datetime: {}".format(
                self.signal_pos["quick"],
                self.signal_pos["medium"],
                self.signal_pos["slow"],
                self.quick_signal.open_price,
                self.quick_signal.close_price,
                self.medium_signal.open_price,
                self.medium_signal.close_price,
                self.slow_signal.open_price,
                self.slow_signal.close_price,
                datetime
            ))
            self.cta_engine.put_strategy_action_event(self, "buy", datetime)
            self.put_event()


    def on_trade(self, trade: TradeData):
        """
        Callback of new trade data update.
        """
        self.put_event()

    def on_stop_order(self, stop_order: StopOrder):
        """
        Callback of stop order update.
        """
        pass
