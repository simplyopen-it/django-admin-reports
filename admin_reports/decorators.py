def register():
    from admin_reports.sites import report_site
    def _report_wrapper(report_class):
        print report_class, report_site
        report_site.register(report_class)
        return report_class
    return _report_wrapper
