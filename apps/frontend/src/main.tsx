import { createRoot } from "react-dom/client";
import { App } from "./App";
import "./styles.css";
async function boot() {
  const root = createRoot(document.getElementById("root")!);
  if (
    import.meta.env.DEV &&
    new URLSearchParams(location.search).get("transport") === "fixtures"
  ) {
    const dev = await import("./dev");
    root.render(
      <App
        transport={dev.transport}
        devTools={{ scenarios: dev.scenarios, select: dev.selectScenario }}
      />,
    );
  } else root.render(<App />);
}
void boot();
