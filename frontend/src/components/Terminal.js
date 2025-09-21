import React, { useEffect, useRef } from "react";
import { Terminal } from "xterm";
import { FitAddon } from "xterm-addon-fit";
import "xterm/css/xterm.css";

const TerminalComponent = () => {
  const terminalRef = useRef(null);
  const term = useRef(null);
  const fitAddon = useRef(null);
  const socketRef = useRef(null);

  useEffect(() => {
    term.current = new Terminal({
      cursorBlink: true,
      fontFamily: "monospace",
      fontSize: 14,
      theme: { background: "#000", foreground: "#fff", cursor: "#fff" },
    });

    fitAddon.current = new FitAddon();
    term.current.loadAddon(fitAddon.current);

    if (terminalRef.current) {
      term.current.open(terminalRef.current);
      fitAddon.current.fit();
    }

    const socket = new WebSocket("ws://localhost:8000");
    socketRef.current = socket;

    let currentLine = "";

    const prompt = (cwd = "$") => {
      term.current.write(`\r\x1b[1;34m${cwd}$ \x1b[0m`);
    };

    socket.onopen = () => {
      term.current.writeln("\x1b[1;32mConnected to Python Terminal\x1b[0m");
      prompt();
    };

    socket.onmessage = (event) => {
      const data = event.data;
      if (!data) return;

      // clear current input line
      for (let i = 0; i < currentLine.length; i++) {
        term.current.write("\b \b");
      }

      // write output line by line
      data.split(/\r?\n/).forEach(line => {
        if (line.trim() !== "") term.current.writeln(line);
      });

      currentLine = ""; // reset current input
      prompt();
    };

    // Handle user input and special keys
    term.current.onKey(({ key, domEvent }) => {
  // Handle Ctrl+C
  if (domEvent.ctrlKey && domEvent.key === "c") {
    // Send special cancel signal to backend
    socket.send("__CTRL_C__");

    // Clear current input line
    for (let i = 0; i < currentLine.length; i++) {
      term.current.write("\b \b");
    }
    currentLine = "";
    term.current.write("^C\r\n"); // like real terminal
    prompt(); // show prompt
    return;
  }

  if (domEvent.key === "Enter") {
    socket.send(currentLine);
    currentLine = "";
    term.current.write("\r\n");
  } else if (domEvent.key === "Backspace") {
    if (currentLine.length > 0) {
      currentLine = currentLine.slice(0, -1);
      term.current.write("\b \b");
    }
  } else if (domEvent.key === "ArrowUp") {
    socket.send("__UP__");
  } else if (domEvent.key === "ArrowDown") {
    socket.send("__DOWN__");
  } else if (domEvent.key === "Tab") {
    domEvent.preventDefault();
    socket.send("__TAB__" + currentLine);
  } else {
    currentLine += key;
    term.current.write(key);
  }
});

    window.addEventListener("resize", () => fitAddon.current.fit());

    return () => {
      window.removeEventListener("resize", () => fitAddon.current.fit());
      socket.close();
      term.current.dispose();
    };
  }, []);

  return <div ref={terminalRef} style={{ width: "100%", height: "100vh" }} />;
};

export default TerminalComponent;
