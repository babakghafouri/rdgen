#!/usr/bin/env python3
"""AdminDesk visual shell patch for RustDesk 1.5.0, applied after ads patch."""
import argparse
from pathlib import Path
p=argparse.ArgumentParser()
p.add_argument('--rustdesk-root',type=Path,required=True)
a=p.parse_args()
home=a.rustdesk_root/'flutter/lib/desktop/pages/desktop_home_page.dart'
s=home.read_text(encoding='utf-8')
start=s.find('  buildRightPane(BuildContext context) {')
end=s.find('\n  buildIDBoard(BuildContext context)',start)
if start<0 or end<0 or 'ConnectionPage()' not in s[start:end]:
    raise SystemExit('Unexpected RustDesk layout: refusing patch')
if 'adminDeskThemeDark' in s: raise SystemExit('Already patched')
new="""  bool adminDeskThemeDark = false;

  Widget _adminDeskCard(Widget child, Color surface, Color outline) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(color: surface,
        borderRadius: BorderRadius.circular(18),
        border: Border.all(color: outline)),
      child: child,
    );
  }

  buildRightPane(BuildContext context) {
    final dark = adminDeskThemeDark;
    final background = dark ? const Color(0xFF111827) : const Color(0xFFF4F7FB);
    final surface = dark ? const Color(0xFF1F2937) : Colors.white;
    final foreground = dark ? Colors.white : const Color(0xFF172B4D);
    final outline = dark ? const Color(0xFF374151) : const Color(0xFFE1E8F2);
    Widget caption(String value) => Text(value,
      style: TextStyle(fontSize: 13, color: foreground.withOpacity(0.72)));
    Widget infoTile(IconData icon, String title, Widget value) => Container(
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(color: background,
        borderRadius: BorderRadius.circular(12)),
      child: Row(children: [
        Icon(icon, color: const Color(0xFF237BEA)),
        const SizedBox(width: 10),
        Expanded(child: Column(crossAxisAlignment: CrossAxisAlignment.start,
          children: [caption(title), const SizedBox(height: 4), value])),
      ]),
    );
    return Container(color: background,
      child: LayoutBuilder(builder: (context, bounds) {
        final compact = bounds.maxWidth < 760;
        final ad = _adminDeskCard(Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('تبلیغات ویژه', style: TextStyle(fontSize: 17,
              fontWeight: FontWeight.bold, color: foreground)),
            const SizedBox(height: 8),
            const AdminDeskAdBanner(),
          ]), surface, outline);
        final device = _adminDeskCard(Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('اطلاعات دستگاه', style: TextStyle(fontSize: 18,
              fontWeight: FontWeight.bold, color: foreground)),
            const SizedBox(height: 12),
            infoTile(Icons.computer, 'نام دستگاه',
              Text(Platform.localHostname, style: TextStyle(color: foreground))),
            const SizedBox(height: 8),
            infoTile(Icons.fingerprint, 'شناسه',
              TextField(controller: gFFI.serverModel.serverId, readOnly: true,
                style: TextStyle(color: foreground),
                decoration: const InputDecoration(isDense: true, border: InputBorder.none))),
            const SizedBox(height: 8),
            infoTile(Icons.circle_outlined, 'وضعیت',
              caption('وضعیت اتصال از بخش اصلی برنامه قابل مشاهده است')),
            const SizedBox(height: 8),
            infoTile(Icons.history, 'آخرین اتصال',
              caption('از تاریخچه اتصال‌ها')),
          ]), surface, outline);
        final remote = _adminDeskCard(const ConnectionPage(), surface, outline);
        return Column(children: [
          Padding(padding: const EdgeInsets.fromLTRB(18, 12, 18, 8),
            child: Row(children: [
              const Icon(Icons.desktop_windows, color: Color(0xFF237BEA), size: 28),
              const SizedBox(width: 9),
              Text('AdminDesk', style: TextStyle(fontSize: 23,
                fontWeight: FontWeight.bold, color: foreground)),
              const Spacer(),
              IconButton(tooltip: dark ? 'حالت روشن' : 'حالت تیره',
                icon: Icon(dark ? Icons.light_mode : Icons.dark_mode, color: foreground),
                onPressed: () => setState(() => adminDeskThemeDark = !dark)),
            ])),
          Expanded(child: Padding(
            padding: const EdgeInsets.fromLTRB(14, 4, 14, 14),
            child: compact
              ? Column(children: [
                  Expanded(child: remote),
                  const SizedBox(height: 10),
                  SizedBox(height: 210, child: SingleChildScrollView(child: device)),
                  const SizedBox(height: 10),
                  SizedBox(height: 190, child: SingleChildScrollView(child: ad)),
                ])
              : Row(crossAxisAlignment: CrossAxisAlignment.stretch, children: [
                  Expanded(flex: 5, child: remote),
                  const SizedBox(width: 12),
                  Expanded(flex: 3, child: SingleChildScrollView(
                    child: Column(children: [device,
                      const SizedBox(height: 12), ad]))),
                ]),
          )),
        ]);
      }));
  }
"""
s=s[:start]+new+s[end:]
home.write_text(s,encoding='utf-8')
print('AdminDesk visual shell applied')
