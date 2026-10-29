"""Small adapter for buttons whose actions may be synchronous or asynchronous."""


class BusyButton:
    _FRAMES = ("⏳", "⌛")

    def __init__(self, widget, label, action, busy_label="Memproses"):
        self.widget = widget
        self.label = label
        self.action = action
        self.busy_label = busy_label
        self.busy = False
        self.enabled = True
        self._timer = None
        self._frame = 0
        self.widget.configure(text=label, command=self.invoke)

    def invoke(self):
        if self.busy:
            return
        self.begin()
        self.widget.after(40, self._run_action)

    def _run_action(self):
        try:
            # Return False when completion will arrive asynchronously.
            if self.action() is not False:
                self.finish()
        except Exception:
            self.finish()

    def begin(self):
        if self.busy:
            return
        self.busy = True
        self.widget.configure(state="disabled")
        self._animate()

    def _animate(self):
        if not self.busy:
            return
        icon = self._FRAMES[self._frame % len(self._FRAMES)]
        self._frame += 1
        self.widget.configure(text=f"{icon} {self.busy_label}")
        self._timer = self.widget.after(350, self._animate)

    def finish(self):
        if not self.busy:
            return
        self.busy = False
        if self._timer is not None:
            try:
                self.widget.after_cancel(self._timer)
            except Exception:
                pass
            self._timer = None
        self.widget.configure(text=self.label, state="normal" if self.enabled else "disabled")

    def set_enabled(self, enabled):
        self.enabled = bool(enabled)
        if not self.busy:
            self.widget.configure(state="normal" if self.enabled else "disabled")
