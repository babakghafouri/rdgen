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

  Widget _adminDeskGlass(Widget child, bool dark) {
    final border = dark ? const Color(0x665BA9F7) : const Color(0x99FFFFFF);
    return ClipRRect(
      borderRadius: BorderRadius.circular(22),
      child: BackdropFilter(
        filter: ImageFilter.blur(sigmaX: 16, sigmaY: 16),
        child: Container(
          decoration: BoxDecoration(
            color: dark ? const Color(0xCC172B49) : const Color(0xDDFBFDFF),
            borderRadius: BorderRadius.circular(22),
            border: Border.all(color: border, width: 1.2),
            boxShadow: [
              BoxShadow(
                color: const Color(0xFF1261B7).withOpacity(dark ? 0.16 : 0.09),
                blurRadius: 24,
                offset: const Offset(0, 9),
              ),
            ],
          ),
          child: child,
        ),
      ),
    );
  }

  buildRightPane(BuildContext context) {
    final dark = adminDeskThemeDark;
    final foreground = dark ? const Color(0xFFF0F7FF) : const Color(0xFF17365B);
    final muted = dark ? const Color(0xFFB5CAE3) : const Color(0xFF56799D);
    final blue = dark ? const Color(0xFF66B6FF) : const Color(0xFF1879D9);
    return Container(
      decoration: BoxDecoration(
        gradient: LinearGradient(
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
          colors: dark
              ? [const Color(0xFF0B1830), const Color(0xFF12345C),
                  const Color(0xFF0D2543)]
              : [const Color(0xFFEAF6FF), const Color(0xFFD5E9FF),
                  const Color(0xFFF5FAFF)],
        ),
      ),
      child: LayoutBuilder(builder: (context, bounds) {
        final compact = bounds.maxWidth < 760;
        final header = Padding(
          padding: const EdgeInsets.fromLTRB(20, 15, 20, 12),
          child: Row(children: [
            Container(
              padding: const EdgeInsets.all(9),
              decoration: BoxDecoration(
                gradient: const LinearGradient(colors: [
                  Color(0xFF1689E9), Color(0xFF0755AE)]),
                borderRadius: BorderRadius.circular(13)),
              child: const Icon(Icons.desktop_windows_rounded,
                  color: Colors.white, size: 22)),
            const SizedBox(width: 11),
            Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
              Text('AdminDesk', style: TextStyle(fontSize: 23,
                  fontWeight: FontWeight.w800, color: foreground)),
              Text('دسترسی سریع و امن', style: TextStyle(
                  fontSize: 11, color: muted)),
            ]),
            const Spacer(),
            IconButton(
              tooltip: dark ? 'حالت روشن' : 'حالت تیره',
              icon: Icon(dark ? Icons.light_mode_rounded
                  : Icons.dark_mode_rounded, color: foreground),
              onPressed: () => setState(() => adminDeskThemeDark = !dark)),
          ]),
        );
        final sessions = _adminDeskGlass(
          Column(crossAxisAlignment: CrossAxisAlignment.stretch, children: [
            Padding(
              padding: const EdgeInsets.fromLTRB(20, 18, 20, 0),
              child: Row(children: [
                Icon(Icons.history_rounded, color: blue, size: 24),
                const SizedBox(width: 9),
                Expanded(child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text('اتصال‌های اخیر', style: TextStyle(
                        fontSize: 19, fontWeight: FontWeight.bold,
                        color: foreground)),
                    Text('Recent Sessions', style: TextStyle(
                        fontSize: 12, color: muted)),
                  ])),
              ]),
            ),
            const SizedBox(height: 6),
            // ConnectionPage contains the real PeerTabPage history,
            // search and connection actions. Never replace it with mock data.
            const Expanded(child: ConnectionPage()),
          ]),
          dark,
        );
        final ads = _adminDeskGlass(
          Column(crossAxisAlignment: CrossAxisAlignment.stretch, children: [
            Padding(
              padding: const EdgeInsets.fromLTRB(17, 17, 17, 10),
              child: Row(children: [
                Icon(Icons.campaign_rounded, color: blue),
                const SizedBox(width: 8),
                Expanded(child: Text('تبلیغات ویژه',
                    style: TextStyle(fontSize: 18,
                        fontWeight: FontWeight.bold, color: foreground))),
              ]),
            ),
            const Padding(
              padding: EdgeInsets.symmetric(horizontal: 12),
              child: AdminDeskAdBanner(),
            ),
            const SizedBox(height: 12),
          ]),
          dark,
        );
        return Column(children: [
          header,
          Expanded(child: Padding(
            padding: const EdgeInsets.fromLTRB(14, 2, 14, 14),
            child: compact
                ? Column(children: [
                    Expanded(flex: 5, child: sessions),
                    const SizedBox(height: 12),
                    Expanded(flex: 3, child: SingleChildScrollView(
                        child: ads)),
                  ])
                : Row(crossAxisAlignment: CrossAxisAlignment.stretch,
                    children: [
                      Expanded(flex: 5, child: sessions),
                      const SizedBox(width: 14),
                      Expanded(flex: 3, child: SingleChildScrollView(
                          child: ads)),
                    ]),
          )),
        ]);
      }),
    );
  }
"""
s=s[:start]+new+s[end:]
if "import 'dart:ui';" not in s:
    s="import 'dart:ui';\n"+s

# Customize the existing RustDesk sidebar without removing ID/password functionality.
old_logo = """      Align(
        alignment: Alignment.center,
        child: loadLogo(),
      ),
      buildTip(context),"""
new_logo = """      Padding(
        padding: const EdgeInsets.fromLTRB(16, 20, 12, 20),
        child: Row(children: [
          Container(
            padding: const EdgeInsets.all(10),
            decoration: BoxDecoration(
              gradient: const LinearGradient(colors: [
                Color(0xFF1689E9), Color(0xFF0755AE)]),
              borderRadius: BorderRadius.circular(14)),
            child: const Icon(Icons.computer_rounded,
                size: 22, color: Colors.white)),
          const SizedBox(width: 10),
          const Expanded(child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text('AdminDesk', style: TextStyle(
                  fontSize: 18, fontWeight: FontWeight.w800,
                  color: Color(0xFF17365B))),
              Text('دسترسی به این دستگاه', style: TextStyle(
                  fontSize: 11, color: Color(0xFF56799D))),
            ])),
        ]),
      ),"""
if old_logo not in s:
    raise SystemExit('Left sidebar logo structure changed')
s=s.replace(old_logo,new_logo,1)
s=s.replace("width: isIncomingOnly ? 280.0 : 200.0,",
            "width: isIncomingOnly ? 280.0 : 245.0,",1)
s=s.replace("color: Theme.of(context).colorScheme.background,",
            "decoration: const BoxDecoration(gradient: LinearGradient(\n"
            "          begin: Alignment.topCenter, end: Alignment.bottomCenter,\n"
            "          colors: [Color(0xFFF6FBFF), Color(0xFFE4F1FF)])),",1)
# Preserve the native recent-peers data source and actions while modernizing cards.
peer_file=a.rustdesk_root/'flutter/lib/common/widgets/peer_card.dart'
peer=peer_file.read_text(encoding='utf-8')
original="color: str2color('${peer.id}${peer.platform}', 0x7f),"
if original not in peer:
    raise SystemExit('Peer card background anchor not found')
peer=peer.replace(original, "color: const Color(0xFF2879B8),")
# All native peer status indicators, click actions, menus and real IDs stay intact.
peer=peer.replace("final double _cardRadius = 16;",
                  "final double _cardRadius = 20;",1)
peer=peer.replace("final double _borderWidth = 2;",
                  "final double _borderWidth = 1.5;",1)
peer_file.write_text(peer,encoding='utf-8')

# Translate the remote ID input label while retaining RustDesk connection behavior.
conn_file=a.rustdesk_root/'flutter/lib/desktop/pages/connection_page.dart'
conn=conn_file.read_text(encoding='utf-8')
conn=conn.replace("translate('Control Remote Desktop')",
                  "'اتصال به دستگاه دیگر'")
conn_file.write_text(conn,encoding='utf-8')

home.write_text(s,encoding='utf-8')
print('AdminDesk visual shell applied')
