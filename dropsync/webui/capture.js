const statusEl = document.querySelector("#status");

function showStatus(message, tone = "info") {
  statusEl.textContent = message;
  statusEl.dataset.tone = tone;
}

async function postJSON(endpoint, payload) {
  const response = await fetch(endpoint, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });
  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || `Request failed: ${response.status}`);
  }
  return response.json();
}

function resetForm(form) {
  form.reset();
}

function handleSubmit(form, handler) {
  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    const formData = new FormData(form);
    showStatus("Sending…");
    try {
      const payload = handler(formData);
      const data = await postJSON(payload.endpoint, payload.body);
      showStatus(`Saved to ${data.path}`, "success");
      resetForm(form);
    } catch (error) {
      console.error(error);
      showStatus(error.message, "error");
    }
  });
}

handleSubmit(document.querySelector("#form-url"), (formData) => ({
  endpoint: "/url",
  body: {
    url: formData.get("url"),
    title: formData.get("title") || undefined,
    selection: formData.get("selection") || undefined,
  },
}));

handleSubmit(document.querySelector("#form-note"), (formData) => ({
  endpoint: "/note",
  body: {
    title: formData.get("title") || undefined,
    body: formData.get("body"),
  },
}));

handleSubmit(document.querySelector("#form-code"), (formData) => ({
  endpoint: "/code",
  body: {
    title: formData.get("title") || undefined,
    lang: formData.get("lang") || undefined,
    code: formData.get("code"),
  },
}));
