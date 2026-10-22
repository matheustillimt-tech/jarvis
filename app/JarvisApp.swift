// JARVIS.app: janela nativa do Mac pro JARVIS.
// Liga o servidor (server.py) quando abre, mostra a esfera numa janela própria,
// libera o microfone e desliga tudo quando você fecha.
// Montar: app/montar.sh

import Cocoa
import WebKit

let telaEspera = """
<html><body style="margin:0;height:100vh;background:#000;color:rgba(255,255,255,.6);display:flex;\
align-items:center;justify-content:center;font:12px -apple-system,system-ui;letter-spacing:.32em;\
text-transform:uppercase"><div style="display:flex;gap:12px;align-items:center"><span style="width:7px;\
height:7px;border-radius:50%;background:#fff;animation:p 1s infinite"></span>ligando o jarvis</div>\
<style>@keyframes p{0%,100%{opacity:.25}50%{opacity:1}}</style></body></html>
"""

func telaErro(_ mensagem: String, log: String) -> String {
    let limpa = { (s: String) in s.replacingOccurrences(of: "&", with: "&amp;").replacingOccurrences(of: "<", with: "&lt;") }
    return """
    <html><body style="margin:0;height:100vh;background:#000;color:#fff;display:flex;align-items:center;\
    justify-content:center;font:15px -apple-system,system-ui;text-align:center"><div style="max-width:560px;\
    padding:24px"><div style="font-size:12px;letter-spacing:.32em;text-transform:uppercase;\
    color:rgba(255,255,255,.6);margin-bottom:18px">jarvis</div><div style="font-size:20px;margin-bottom:14px">\
    \(limpa(mensagem))</div><div style="color:rgba(255,255,255,.55);line-height:1.6">Detalhes em \
    <code>\(limpa(log))</code><br>Aperte ⌘R pra tentar de novo.</div></div></body></html>
    """
}

final class AppDelegate: NSObject, NSApplicationDelegate, WKUIDelegate, WKNavigationDelegate {
    var janela: NSWindow!
    var web: WKWebView!
    var servidor: Process?
    var encerrando = false
    var tentativas = 0

    let pasta = Bundle.main.object(forInfoDictionaryKey: "JarvisPasta") as? String ?? ""
    let porta = Bundle.main.object(forInfoDictionaryKey: "JarvisPorta") as? String ?? "8790"
    var base: URL { URL(string: "http://localhost:\(porta)/")! }
    var caminhoLog: String { (pasta as NSString).appendingPathComponent(".estado/app.log") }

    func applicationDidFinishLaunching(_ notification: Notification) {
        montarMenu()
        montarJanela()
        web.loadHTMLString(telaEspera, baseURL: nil)
        checar { noAr in
            if !noAr { self.iniciarServidor() }
            self.esperar()
        }
    }

    func applicationShouldTerminateAfterLastWindowClosed(_ sender: NSApplication) -> Bool { true }

    func applicationWillTerminate(_ notification: Notification) {
        encerrando = true
        guard let p = servidor, p.isRunning else { return }
        p.terminate()  // o servidor fecha o Claude Code junto
        let limite = Date().addingTimeInterval(4)
        while p.isRunning && Date() < limite { usleep(100_000) }
    }

    // MARK: janela

    func montarJanela() {
        let config = WKWebViewConfiguration()
        config.mediaTypesRequiringUserActionForPlayback = []
        web = WKWebView(frame: .zero, configuration: config)
        web.uiDelegate = self
        web.navigationDelegate = self
        web.setValue(false, forKey: "drawsBackground")
        if #available(macOS 13.3, *) { web.isInspectable = true }

        janela = NSWindow(
            contentRect: NSRect(x: 0, y: 0, width: 1100, height: 760),
            styleMask: [.titled, .closable, .miniaturizable, .resizable, .fullSizeContentView],
            backing: .buffered, defer: false)
        janela.title = "JARVIS"
        janela.titlebarAppearsTransparent = true
        janela.titleVisibility = .hidden
        janela.backgroundColor = .black
        janela.appearance = NSAppearance(named: .darkAqua)
        janela.minSize = NSSize(width: 480, height: 360)
        janela.collectionBehavior = [.fullScreenPrimary]
        janela.isReleasedWhenClosed = false
        janela.contentView = web
        janela.center()
        janela.setFrameAutosaveName("JarvisJanela")
        janela.makeKeyAndOrderFront(nil)
        NSApp.activate(ignoringOtherApps: true)
    }

    func montarMenu() {
        let principal = NSMenu()

        let appItem = NSMenuItem()
        let appMenu = NSMenu()
        appMenu.addItem(withTitle: "Sobre o JARVIS", action: #selector(NSApplication.orderFrontStandardAboutPanel(_:)), keyEquivalent: "")
        appMenu.addItem(.separator())
        appMenu.addItem(withTitle: "Ocultar JARVIS", action: #selector(NSApplication.hide(_:)), keyEquivalent: "h")
        appMenu.addItem(.separator())
        appMenu.addItem(withTitle: "Encerrar JARVIS", action: #selector(NSApplication.terminate(_:)), keyEquivalent: "q")
        appItem.submenu = appMenu
        principal.addItem(appItem)

        let editarItem = NSMenuItem()
        let editar = NSMenu(title: "Editar")
        editar.addItem(withTitle: "Desfazer", action: Selector(("undo:")), keyEquivalent: "z")
        editar.addItem(.separator())
        editar.addItem(withTitle: "Recortar", action: #selector(NSText.cut(_:)), keyEquivalent: "x")
        editar.addItem(withTitle: "Copiar", action: #selector(NSText.copy(_:)), keyEquivalent: "c")
        editar.addItem(withTitle: "Colar", action: #selector(NSText.paste(_:)), keyEquivalent: "v")
        editar.addItem(withTitle: "Selecionar tudo", action: #selector(NSText.selectAll(_:)), keyEquivalent: "a")
        editarItem.submenu = editar
        principal.addItem(editarItem)

        let verItem = NSMenuItem()
        let ver = NSMenu(title: "Ver")
        ver.addItem(withTitle: "Recarregar", action: #selector(recarregar), keyEquivalent: "r")
        let cheia = NSMenuItem(title: "Tela cheia", action: #selector(NSWindow.toggleFullScreen(_:)), keyEquivalent: "f")
        cheia.keyEquivalentModifierMask = [.command, .control]
        ver.addItem(cheia)
        verItem.submenu = ver
        principal.addItem(verItem)

        NSApp.mainMenu = principal
    }

    // MARK: servidor

    func checar(_ fim: @escaping (Bool) -> Void) {
        var req = URLRequest(url: base.appendingPathComponent("api/saude"))
        req.timeoutInterval = 1
        URLSession.shared.dataTask(with: req) { _, resposta, _ in
            let ok = (resposta as? HTTPURLResponse)?.statusCode == 200
            DispatchQueue.main.async { fim(ok) }
        }.resume()
    }

    func esperar() {
        checar { ok in
            if ok {
                self.web.load(URLRequest(url: self.base))
                return
            }
            self.tentativas += 1
            if self.tentativas > 120 {
                self.mostrarErro("O JARVIS não ligou em 60 segundos.")
                return
            }
            DispatchQueue.main.asyncAfter(deadline: .now() + 0.5) { self.esperar() }
        }
    }

    func iniciarServidor() {
        let estado = (pasta as NSString).appendingPathComponent(".estado")
        try? FileManager.default.createDirectory(atPath: estado, withIntermediateDirectories: true)
        FileManager.default.createFile(atPath: caminhoLog, contents: nil)
        let log = FileHandle(forWritingAtPath: caminhoLog)

        let p = Process()
        // Shell de login interativo: carrega o PATH do .zshrc (onde costuma estar o claude).
        p.executableURL = URL(fileURLWithPath: "/bin/zsh")
        let seguro = pasta.replacingOccurrences(of: "'", with: "'\\''")
        p.arguments = ["-lic", "cd '\(seguro)' && exec python3 server.py --sem-abrir"]
        p.standardInput = FileHandle.nullDevice
        if let log = log {
            p.standardOutput = log
            p.standardError = log
        }
        p.terminationHandler = { [weak self] processo in
            DispatchQueue.main.async {
                guard let self = self, !self.encerrando else { return }
                self.servidor = nil
                self.mostrarErro("O JARVIS parou (código \(processo.terminationStatus)).")
            }
        }
        do {
            try p.run()
            servidor = p
        } catch {
            mostrarErro("Não consegui ligar o JARVIS: \(error.localizedDescription)")
        }
    }

    func mostrarErro(_ mensagem: String) {
        web.loadHTMLString(telaErro(mensagem, log: caminhoLog), baseURL: nil)
    }

    @objc func recarregar() {
        tentativas = 0
        checar { ok in
            if ok {
                self.web.load(URLRequest(url: self.base))
            } else {
                self.web.loadHTMLString(telaEspera, baseURL: nil)
                if self.servidor?.isRunning != true { self.iniciarServidor() }
                self.esperar()
            }
        }
    }

    // MARK: microfone e links

    @available(macOS 12.0, *)
    func webView(_ webView: WKWebView, requestMediaCapturePermissionFor origin: WKSecurityOrigin,
                 initiatedByFrame frame: WKFrameInfo, type: WKMediaCaptureType,
                 decisionHandler: @escaping (WKPermissionDecision) -> Void) {
        decisionHandler(origin.host == "localhost" || origin.host == "127.0.0.1" ? .grant : .deny)
    }

    func webView(_ webView: WKWebView, decidePolicyFor navigationAction: WKNavigationAction,
                 decisionHandler: @escaping (WKNavigationActionPolicy) -> Void) {
        if let url = navigationAction.request.url, let host = url.host,
           host != "localhost", host != "127.0.0.1", navigationAction.navigationType == .linkActivated {
            NSWorkspace.shared.open(url)
            decisionHandler(.cancel)
            return
        }
        decisionHandler(.allow)
    }
}

let app = NSApplication.shared
let delegado = AppDelegate()
app.delegate = delegado
app.setActivationPolicy(.regular)
app.run()
