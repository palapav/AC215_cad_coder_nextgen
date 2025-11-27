export {};

/* Same generation logic is handled inside AIModelSandbox.tsx. This is not used for now.
export async function generateCADCode(prompt: string, model: string) {
    const response = await fetch("http://localhost:8000/generate_cad", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        image_url: "dummy.png",
        model_choice: model,
        prompt: prompt,
      }),
    });
    return response.json();
  }
*/