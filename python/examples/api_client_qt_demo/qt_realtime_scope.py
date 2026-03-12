"""QT Realtime Scope."""
#-------------------------------------------------------------------------------
# Name:         qt_real_time_scope
#
# Purpose:      QT Realtime Scope
#
# Note          Checked with Python 3.11.9
#
# Author:       rosettacnc-classroom@gmail.com
#
# Created:      11/03/2026
# Copyright:    RosettaCNC (c) 2016-2026
# Licence:      RosettaCNC License 1.0 (RCNC-1.0)
# Coding Style  https://www.python.org/dev/peps/pep-0008/
#-------------------------------------------------------------------------------
import time
import numpy as np
import pyqtgraph as pg


def _build_channel_names(channels: int, channel_names=None):
    """Return validated channel names."""
    if channel_names is None:
        return [f"CH{ch + 1}" for ch in range(channels)]

    try:
        names = list(channel_names)
    except TypeError as exc:
        raise TypeError("channel_names must be a sequence or None") from exc

    if len(names) != channels:
        raise ValueError(f"channel_names length must be {channels}, got {len(names)}")

    return [str(name) for name in names]


def _ensure_legend(
    widget: pg.PlotWidget,
    legend_anchor=(1, 0),
    legend_offset=(-10, 10),
    legend_bg=(20, 20, 20, 180),
    legend_border=(200, 200, 200, 120),
    legend_text_color="white",
):
    """Create and configure the legend only once for the target PlotWidget."""
    plot_item = widget.getPlotItem()

    if plot_item.legend is None:
        plot_item.addLegend()

    legend = plot_item.legend

    if legend is not None:
        legend.anchor(
            itemPos=legend_anchor,
            parentPos=legend_anchor,
            offset=legend_offset,
        )
        legend.setBrush(pg.mkBrush(*legend_bg))
        legend.setPen(pg.mkPen(*legend_border))

        for sample, label in legend.items:
            label.setText(label.text, color=legend_text_color)

    return plot_item


class QRealTimeScope:
    """Xxx..."""

    def __init__(
        self,
        widget: pg.PlotWidget,
        channels: int,
        samples: int,
        channel_names=None,
        legend_anchor=(1, 0),
        legend_offset=(-10, 10),
        legend_bg=(20, 20, 20, 180),
        legend_border=(200, 200, 200, 120),
        legend_text_color="white",
    ):
        if not isinstance(widget, pg.PlotWidget):
            raise TypeError(f"widget must be PlotWidget, got {type(widget).__name__}")

        if not isinstance(channels, int) or isinstance(channels, bool):
            raise TypeError(f"channels must be int, got {type(channels).__name__}")

        if not isinstance(samples, int) or isinstance(samples, bool):
            raise TypeError(f"samples must be int, got {type(samples).__name__}")

        if channels <= 0:
            raise ValueError("channels must be > 0")

        if samples <= 1:
            raise ValueError("samples must be > 1")

        self.widget = widget
        self.channels = channels
        self.samples = samples
        self.channel_names = _build_channel_names(channels, channel_names)

        # enable antialiasing and OpenGL support
        pg.setConfigOptions(antialias=True)
        pg.setConfigOptions(useOpenGL=True)

        # remove tick and number from bottom axis (ruler)
        ax = self.widget.getPlotItem().getAxis('bottom')
        ax.setTicks([])
        ax.setStyle(showValues=False)

        # set channels color
        self.colors = [
            pg.mkPen(color=(0, 255, 0), width=1),
            pg.mkPen(color=(255, 255, 0), width=1),
            pg.mkPen(color=(0, 200, 255), width=1),
            pg.mkPen(color=(255, 0, 255), width=1),
            pg.mkPen(color=(255, 128, 0), width=1),
            pg.mkPen(color=(255, 255, 255), width=1),
        ]

        # plot performance / behavior tweaks
        self.widget.setClipToView(True)
        self.widget.setDownsampling(mode="peak")
        self.widget.setRange(xRange=(0, self.samples - 1), padding=0)
        self.widget.setMouseEnabled(x=False, y=False)

        # set y width to fixed size (in pixel)
        axis_y = self.widget.getPlotItem().getAxis('left')
        axis_y.setWidth(50)

        # ring buffer state
        self._head = 0
        self._filled = False

        # X axis (fixed)
        self._x = np.arange(self.samples, dtype=np.float32)

        # data buffer (channels x samples)
        self._buf = np.zeros((self.channels, self.samples), dtype=np.float32)

        # preallocated "view" buffer to avoid np.concatenate allocations
        self._view = np.empty((self.channels, self.samples), dtype=np.float32)

        # one curve per channel (created once)
        self._plot_item = _ensure_legend(
            self.widget,
            legend_anchor=legend_anchor,
            legend_offset=legend_offset,
            legend_bg=legend_bg,
            legend_border=legend_border,
            legend_text_color=legend_text_color,
        )
        self._curves = [
            self.widget.plot(
                self._x,
                self._buf[ch],
                pen=self.colors[ch],
                name=self.channel_names[ch],
            )
            for ch in range(self.channels)
        ]
        self._refresh_legend_style(
            legend_anchor=legend_anchor,
            legend_offset=legend_offset,
            legend_bg=legend_bg,
            legend_border=legend_border,
            legend_text_color=legend_text_color,
        )

    def _refresh_legend_style(
        self,
        legend_anchor=(1, 0),
        legend_offset=(-10, 10),
        legend_bg=(20, 20, 20, 180),
        legend_border=(200, 200, 200, 120),
        legend_text_color="white",
    ):
        """Refresh legend style after curves have been created."""
        _ensure_legend(
            self.widget,
            legend_anchor=legend_anchor,
            legend_offset=legend_offset,
            legend_bg=legend_bg,
            legend_border=legend_border,
            legend_text_color=legend_text_color,
        )

    def push(self, values):
        """
        Push one sample per channel.
        values: sequence (list/tuple/np.ndarray) length == channels
        """
        if values is None:
            raise TypeError("values must be a sequence, got None")

        # fast length check (works for list/tuple/np.ndarray)
        try:
            n = len(values)
        except TypeError:
            raise TypeError(f"values must be a sequence, got {type(values).__name__}")

        if n != self.channels:
            raise ValueError(f"values length must be {self.channels}, got {n}")

        # convert to float32 without unnecessary copies if possible
        v = np.asarray(values, dtype=np.float32)

        h = self._head

        # write one column (one sample for all channels)
        self._buf[:, h] = v

        # advance head
        h += 1
        if h >= self.samples:
            h = 0
            self._filled = True
        self._head = h

        # build left-to-right view without shifting or concatenating
        if self._filled:
            k = h  # cut index
            self._view[:, :self.samples - k] = self._buf[:, k:]
            self._view[:, self.samples - k:] = self._buf[:, :k]
            y = self._view
        else:
            y = self._buf

        # update curves
        for ch, curve in enumerate(self._curves):
            curve.setData(self._x, y[ch])

    def clear(self):
        """Clear buffer and restart from empty state."""
        self._buf.fill(0.0)
        self._head = 0
        self._filled = False
        for ch, curve in enumerate(self._curves):
            curve.setData(self._x, self._buf[ch])


class QRealTimeScopeSynched:
    def __init__(
        self,
        widget: pg.PlotWidget,
        channels: int,
        samples: int,
        channel_names=None,
        legend_anchor=(1, 0),
        legend_offset=(-10, 10),
        legend_bg=(20, 20, 20, 180),
        legend_border=(200, 200, 200, 120),
        legend_text_color="white",
    ):
        if not isinstance(widget, pg.PlotWidget):
            raise TypeError(f"widget must be PlotWidget, got {type(widget).__name__}")

        if not isinstance(channels, int) or isinstance(channels, bool):
            raise TypeError(f"channels must be int, got {type(channels).__name__}")

        if not isinstance(samples, int) or isinstance(samples, bool):
            raise TypeError(f"samples must be int, got {type(samples).__name__}")

        if channels <= 0:
            raise ValueError("channels must be > 0")

        if samples <= 1:
            raise ValueError("samples must be > 1")

        self.widget = widget
        self.channels = channels
        self.samples = samples
        self.channel_names = _build_channel_names(channels, channel_names)

        # plot behavior/perf
        self.widget.setClipToView(True)
        self.widget.setDownsampling(mode="peak")
        self.widget.setMouseEnabled(x=False, y=False)

        # ring buffer state
        self._head = 0
        self._filled = False

        # buffers
        self._t = np.zeros(self.samples, dtype=np.float64)                 # timestamps
        self._buf = np.zeros((self.channels, self.samples), dtype=np.float32)

        # preallocated views (avoid allocations each push)
        self._t_view = np.empty(self.samples, dtype=np.float64)
        self._y_view = np.empty((self.channels, self.samples), dtype=np.float32)

        # curves (one per channel)
        self._plot_item = _ensure_legend(
            self.widget,
            legend_anchor=legend_anchor,
            legend_offset=legend_offset,
            legend_bg=legend_bg,
            legend_border=legend_border,
            legend_text_color=legend_text_color,
        )
        self._curves = [
            self.widget.plot(
                self._t,
                self._buf[ch],
                pen=pg.mkPen(width=1),
                name=self.channel_names[ch],
            )
            for ch in range(self.channels)
        ]
        self._refresh_legend_style(
            legend_anchor=legend_anchor,
            legend_offset=legend_offset,
            legend_bg=legend_bg,
            legend_border=legend_border,
            legend_text_color=legend_text_color,
        )

        # optional: keep a rolling visible time window (seconds).
        # if None -> auto range based on all visible points.
        self.time_window_s = None

        # for sanity check on time ordering (optional)
        self._last_t = None

    def _refresh_legend_style(
        self,
        legend_anchor=(1, 0),
        legend_offset=(-10, 10),
        legend_bg=(20, 20, 20, 180),
        legend_border=(200, 200, 200, 120),
        legend_text_color="white",
    ):
        """Refresh legend style after curves have been created."""
        _ensure_legend(
            self.widget,
            legend_anchor=legend_anchor,
            legend_offset=legend_offset,
            legend_bg=legend_bg,
            legend_border=legend_border,
            legend_text_color=legend_text_color,
        )

    def push(self, values, t=None):
        """
        Push one sample per channel with timestamp.
        values: sequence length == channels
        t: float timestamp (seconds). If None -> time.monotonic()
        """
        if t is None:
            t = time.monotonic()
        else:
            # accept int/float/np number
            if not isinstance(t, (int, float, np.floating, np.integer)) or isinstance(t, bool):
                raise TypeError(f"t must be a number (seconds), got {type(t).__name__}")
            t = float(t)

        # optional: enforce non-decreasing time (helps display)
        if self._last_t is not None and t < self._last_t:
            # If packets arrive out-of-order, you can either:
            # - clamp: t = self._last_t
            # - ignore the sample
            # Here we clamp to keep the plot sane
            t = self._last_t
        self._last_t = t

        try:
            n = len(values)
        except TypeError:
            raise TypeError(f"values must be a sequence, got {type(values).__name__}")

        if n != self.channels:
            raise ValueError(f"values length must be {self.channels}, got {n}")

        v = np.asarray(values, dtype=np.float32)

        h = self._head

        # write into ring buffers
        self._t[h] = t
        self._buf[:, h] = v

        # advance head
        h += 1
        if h >= self.samples:
            h = 0
            self._filled = True
        self._head = h

        # build left-to-right views (timestamps + signals)
        if self._filled:
            k = h
            self._t_view[:self.samples - k] = self._t[k:]
            self._t_view[self.samples - k:] = self._t[:k]

            self._y_view[:, :self.samples - k] = self._buf[:, k:]
            self._y_view[:, self.samples - k:] = self._buf[:, :k]

            x = self._t_view
            y = self._y_view
        else:
            x = self._t
            y = self._buf

        # update curves with real X
        for ch, curve in enumerate(self._curves):
            curve.setData(x, y[ch])

        # optional: show only last "time_window_s" seconds
        if self.time_window_s is not None:
            t_max = x[-1]
            self.widget.setXRange(t_max - self.time_window_s, t_max, padding=0)

    def clear(self):
        self._t.fill(0.0)
        self._buf.fill(0.0)
        self._head = 0
        self._filled = False
        self._last_t = None
        for ch, curve in enumerate(self._curves):
            curve.setData(self._t, self._buf[ch])
