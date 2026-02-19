import time
import numpy as np
import pyqtgraph as pg


class QRealTimeScope:
    def __init__(self, widget: pg.PlotWidget, channels: int, samples: int):
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

        # enable antialiasing and OpenGL support
        pg.setConfigOptions(antialias=True)
        pg.setConfigOptions(useOpenGL=True)

        # remove tick and number from bottom axis (ruler)
        ax = self.widget.getPlotItem().getAxis('bottom')
        ax.setTicks([])
        ax.setStyle(showValues=False)

        #
        #self.widget.getPlotItem().layout.setRowFixedHeight(3, 0)  # spesso la row dell’asse bottom è 3

        # set channels color
        self.colors = [
            pg.mkPen(color=(0, 255, 0)),
            pg.mkPen(color=(255, 255, 0)),
            pg.mkPen(color=(0, 200, 255)),
            pg.mkPen(color=(255, 0, 255)),
            pg.mkPen(color=(255, 128, 0)),
            pg.mkPen(color=(255, 255, 255)),
        ]

        # Plot performance / behavior tweaks
        self.widget.setClipToView(True)
        self.widget.setDownsampling(mode="peak")
        self.widget.setRange(xRange=(0, self.samples - 1))
        self.widget.setMouseEnabled(x=False, y=False)

        # set y range in fixed mode
        """
        self.widget.enableAutoRange('y', False)
        self.widget.setYRange(-100.0, 100.0, padding=0)
        """

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
        self._curves = [
            self.widget.plot(self._x, self._buf[ch], pen=self.colors[ch])
            for ch in range(self.channels)
        ]

    def push(self, values):
        """
        Push one sample per channel.
        values: sequence (list/tuple/np.ndarray) length == channels
        """
        if values is None:
            raise TypeError("values must be a sequence, got None")

        # Fast length check (works for list/tuple/np.ndarray)
        try:
            n = len(values)
        except TypeError:
            raise TypeError(f"values must be a sequence, got {type(values).__name__}")

        if n != self.channels:
            raise ValueError(f"values length must be {self.channels}, got {n}")

        # Convert to float32 without unnecessary copies if possible
        v = np.asarray(values, dtype=np.float32)

        h = self._head

        # Write one column (one sample for all channels)
        self._buf[:, h] = v

        # Advance head
        h += 1
        if h >= self.samples:
            h = 0
            self._filled = True
        self._head = h

        # Build left-to-right view without shifting or concatenating
        if self._filled:
            k = h  # cut index
            self._view[:, :self.samples - k] = self._buf[:, k:]
            self._view[:, self.samples - k:] = self._buf[:, :k]
            y = self._view
        else:
            y = self._buf

        # Update curves
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
    def __init__(self, widget: pg.PlotWidget, channels: int, samples: int):
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

        # Plot behavior/perf
        self.widget.setClipToView(True)
        self.widget.setDownsampling(mode="peak")
        self.widget.setMouseEnabled(x=False, y=False)

        # Ring buffer state
        self._head = 0
        self._filled = False

        # Buffers
        self._t = np.zeros(self.samples, dtype=np.float64)                 # timestamps
        self._buf = np.zeros((self.channels, self.samples), dtype=np.float32)

        # Preallocated views (avoid allocations each push)
        self._t_view = np.empty(self.samples, dtype=np.float64)
        self._y_view = np.empty((self.channels, self.samples), dtype=np.float32)

        # Curves (one per channel)
        self._curves = [
            self.widget.plot(self._t, self._buf[ch], pen=pg.mkPen(width=1))
            for ch in range(self.channels)
        ]

        # Optional: keep a rolling visible time window (seconds).
        # If None -> auto range based on all visible points.
        self.time_window_s = None

        # For sanity check on time ordering (optional)
        self._last_t = None

    def push(self, values, t=None):
        """
        Push one sample per channel with timestamp.
        values: sequence length == channels
        t: float timestamp (seconds). If None -> time.monotonic()
        """
        if t is None:
            t = time.monotonic()
        else:
            # Accept int/float/np number
            if not isinstance(t, (int, float, np.floating, np.integer)) or isinstance(t, bool):
                raise TypeError(f"t must be a number (seconds), got {type(t).__name__}")
            t = float(t)

        # Optional: enforce non-decreasing time (helps display)
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

        # Write into ring buffers
        self._t[h] = t
        self._buf[:, h] = v

        # Advance head
        h += 1
        if h >= self.samples:
            h = 0
            self._filled = True
        self._head = h

        # Build left-to-right views (timestamps + signals)
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

        # Update curves with real X
        for ch, curve in enumerate(self._curves):
            curve.setData(x, y[ch])

        # Optional: show only last "time_window_s" seconds
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
