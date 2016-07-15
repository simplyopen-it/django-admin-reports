def register():
    from .sites import site
    def _report_wrapper(report_class):
        site.register(report_class)
        return report_class
    return _report_wrapper
