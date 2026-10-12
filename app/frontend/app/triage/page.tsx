"use client";

import { useEffect, useMemo, useState } from "react";
import { useLang } from "../i18n";
import "./triage.css";

declare global {
  interface Window { SpeechRecognition?: new () => SpeechRecognition; webkitSpeechRecognition?: new () => SpeechRecognition; }
  interface SpeechRecognition extends EventTarget { lang: string; interimResults: boolean; continuous: boolean; onresult: ((event: SpeechRecognitionEvent) => void) | null; onerror: (() => void) | null; onend: (() => void) | null; start(): void; stop(): void; }
  interface SpeechRecognitionEvent extends Event { results: { [index: number]: { [index: number]: { transcript: string } } } }
}

type Mode = "self" | "caregiver";
type Question = { id: string; type: "choice" | "multi" | "text"; text: Record<string, string>; options: { value: string; zh: string; en: string }[] };
type Analysis = { product?: { name?: string | null; brand?: string | null; category?: string | null }; ingredients?: { name: string; confidence?: number }[]; risk_level?: string; summary?: string };
type TriageState = { case_id: string; mode: Mode; answers: Record<string, unknown>; analysis?: Analysis | null; next_question?: Question | null; result?: { level: string; reason: string; actions: string[]; disclaimer?: string } | null };

const LEVEL: Record<string, { en: string; zh: string }> = {
  emergency: { en: "EMERGENCY", zh: "危急" }, urgent: { en: "URGENT", zh: "紧急" }, moderate: { en: "MODERATE", zh: "中等" }, low: { en: "LOW", zh: "低风险" }, unknown: { en: "UNKNOWN", zh: "暂无法判断" },
};

function speak(text: string, lang: "zh" | "en") {
  if (typeof window === "undefined" || !("speechSynthesis" in window)) return false;
  window.speechSynthesis.cancel();
  const utterance = new SpeechSynthesisUtterance(text);
  utterance.lang = lang === "zh" ? "zh-CN" : "en-US";
  utterance.rate = 0.9;
  window.speechSynthesis.speak(utterance);
  return true;
}

export default function TriagePage() {
  const { lang } = useLang();
  const zh = lang === "zh";
  const [mode, setMode] = useState<Mode | null>(null);
  const [elderMode, setElderMode] = useState(false);
  const [state, setState] = useState<TriageState | null>(null);
  const [analysis, setAnalysis] = useState<Analysis | null>(null);
  const [navigation, setNavigation] = useState<any>(null);
  const [selected, setSelected] = useState<string[]>([]);
  const [text, setText] = useState("");
  const [busy, setBusy] = useState(false);
  const [listening, setListening] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    try {
      const raw = window.localStorage.getItem("bottlesafe:last-analysis");
      if (raw) setAnalysis(JSON.parse(raw) as Analysis);
      setElderMode(window.localStorage.getItem("bottlesafe:elder-mode") === "1");
    } catch { setAnalysis(null); }
    return () => { if ("speechSynthesis" in window) window.speechSynthesis.cancel(); };
  }, []);

  const question = state?.next_question;
  const productName = analysis?.product?.name || (zh ? "未确认产品" : "Product not confirmed");
  const questionSpeech = useMemo(() => {
    if (!question) return "";
    const choices = question.options.map((option) => option[lang]).join(zh ? "。" : ". ");
    return `${question.text[lang]}${choices ? ` ${choices}` : ""}`;
  }, [question, lang, zh]);

  function selectMode(next: Mode) { setMode(next); setElderMode(next === "caregiver" ? true : elderMode); }
  function toggleElder(next: boolean) { setElderMode(next); try { window.localStorage.setItem("bottlesafe:elder-mode", next ? "1" : "0"); } catch {} }

  async function start() {
    if (!mode) return;
    setBusy(true); setError(null);
    try {
      const response = await fetch("/api/triage/start", { method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify({ lang, mode, analysis }) });
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || `Request failed (${response.status})`);
      setState(data); setSelected([]); setText("");
    } catch (e) { setError(e instanceof Error ? e.message : String(e)); } finally { setBusy(false); }
  }

  async function next() {
    if (!state || !question) return;
    const answer = question.type === "multi" ? selected : question.type === "text" ? text.trim() : selected[0];
    if ((Array.isArray(answer) && answer.length === 0) || (!Array.isArray(answer) && !answer)) { setError(zh ? "请先回答当前问题。" : "Please answer this question first."); return; }
    setBusy(true); setError(null);
    try {
      const response = await fetch("/api/triage/answer", { method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify({ case_id: state.case_id, question_id: question.id, answer, analysis }) });
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || `Request failed (${response.status})`);
      setState(data);
      if (data.result) {
        const navResponse = await fetch("/api/triage/navigate", { method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify({ case_id: data.case_id, lang }) });
        const navData = await navResponse.json();
        if (!navResponse.ok) throw new Error(navData.detail || `Navigation failed (${navResponse.status})`);
        setNavigation(navData);
      }
      setSelected([]); setText("");
    } catch (e) { setError(e instanceof Error ? e.message : String(e)); } finally { setBusy(false); }
  }

  function startVoiceInput() {
    const Recognition = typeof window !== "undefined" ? (window.SpeechRecognition || window.webkitSpeechRecognition) : undefined;
    if (!Recognition) { setError(zh ? "当前浏览器不支持语音输入，请使用大按钮选择或键盘输入。" : "Voice input is not supported in this browser. Use the large buttons or keyboard."); return; }
    const recognition = new Recognition(); recognition.lang = zh ? "zh-CN" : "en-US"; recognition.interimResults = false; recognition.continuous = false;
    recognition.onresult = (event) => {
      const transcript = event.results[0][0].transcript.trim();
      if (!question || question.type === "text") {
        setText(transcript);
      } else {
        const normalized = transcript.toLocaleLowerCase();
        const matches = question.options.filter((option) => {
          const label = option[lang].toLocaleLowerCase();
          return normalized.includes(label) || normalized.includes(option.value.toLocaleLowerCase());
        }).map((option) => option.value);
        if (matches.length) setSelected(question.type === "multi" ? matches : [matches[0]]);
        else setError(zh ? `听到“${transcript}”，请点选对应的大按钮确认。` : `I heard “${transcript}”. Please confirm with a large button.`);
      }
      setListening(false);
    };
    recognition.onerror = () => { setListening(false); setError(zh ? "没有听清，请再试一次。" : "I could not hear that. Please try again."); };
    recognition.onend = () => setListening(false);
    setListening(true); recognition.start();
  }
  async function shareResult() {
    const level = state?.result ? (LEVEL[state.result.level]?.[lang] || state.result.level) : "";
    const message = `${level}\n${state?.result?.reason || ""}\n${state?.result?.actions.join("\n") || ""}`;
    try {
      if (navigator.share) await navigator.share({ title: "BottleSafe triage", text: message });
      else { await navigator.clipboard?.writeText(message); setError(zh ? "结果已复制，可以发给家人。" : "Result copied. You can send it to a helper."); }
    } catch {}
  }

  const emergency = state?.result?.level === "emergency";
  return (
    <main className={`triage-page${elderMode ? " elder-mode" : ""}${mode === "caregiver" ? " caregiver-mode" : ""}`}>
      <a className="triage-back" href="/scan">← {zh ? "返回识别" : "Back to scan"}</a>
      <header className="triage-header">
        <p className="triage-kicker">Healthcare Challenge 1 · AI Grandma Knows Best</p>
        <h1>{zh ? "化学品暴露安全分诊" : "Chemical exposure safety triage"}</h1>
        <p>{zh ? "每页只回答一个问题。大按钮、简单语言和语音辅助，帮助老人和家属更快求助。" : "One question per page. Large buttons, simple words and voice help for older adults and family caregivers."}</p>
      </header>

      {!mode && !state && (
        <section className="mode-card" aria-labelledby="mode-title">
          <h2 id="mode-title">{zh ? "你现在是谁？" : "Who are you helping?"}</h2>
          <button className="mode-button" onClick={() => selectMode("self")}><b>{zh ? "我是受影响者" : "I am the exposed person"}</b><span>{zh ? "我正在回答自己的情况" : "I am answering for myself"}</span></button>
          <button className="mode-button" onClick={() => selectMode("caregiver")}><b>{zh ? "我在帮助别人" : "I am helping someone"}</b><span>{zh ? "家属、照护者或身边的陪同者" : "A family member, caregiver or helper"}</span></button>
          <label className="elder-toggle"><input type="checkbox" checked={elderMode} onChange={(e) => toggleElder(e.target.checked)} /> <span>{zh ? "老年人模式：大字号 + 高对比度" : "Older adult mode: large text + high contrast"}</span></label>
        </section>
      )}

      {mode && !state && (
        <section className="start-card">
          <p className="mode-badge">{mode === "caregiver" ? (zh ? "家庭照护者模式" : "Family caregiver mode") : (zh ? "本人模式" : "Self mode")}</p>
          <h2>{zh ? "准备好了吗？" : "Ready to begin?"}</h2>
          <p>{mode === "caregiver" ? (zh ? "我们会逐页询问年龄、清醒程度、呼吸、陪同、是否拨打急救电话和是否分享结果。" : "We will ask about age, alertness, breathing, company, calling emergency services and sharing the result.") : (zh ? "我们会逐页询问暴露方式、症状、年龄和基础疾病。" : "We will ask about exposure, symptoms, age and health conditions, one page at a time.")}</p>
          <div className="start-actions"><button className="primary-button" disabled={busy} onClick={() => void start()}>{busy ? (zh ? "正在开始…" : "Starting…") : (zh ? "开始分诊" : "Start triage")}</button><button className="secondary-button" onClick={() => setMode(null)}>{zh ? "返回选择" : "Change mode"}</button></div>
        </section>
      )}

      {state && !state.result && question && (
        <section className="question-card" aria-live="polite">
          <div className="question-meta"><span>{mode === "caregiver" ? (zh ? "照护者模式" : "Caregiver mode") : (zh ? "本人模式" : "Self mode")}</span><span>{zh ? "一页一个问题" : "One question"}</span></div>
          <h2>{question.text[lang]}</h2>
          <div className="voice-actions"><button className="voice-button" onClick={() => speak(questionSpeech, lang)} aria-label={zh ? "朗读问题" : "Read question aloud"}>🔊 {zh ? "朗读问题" : "Read aloud"}</button><button className={`voice-button${listening ? " listening" : ""}`} onClick={startVoiceInput} aria-label={zh ? "语音回答当前问题" : "Answer this question by voice"}>🎙 {listening ? (zh ? "正在听…" : "Listening…") : (question.type === "text" ? (zh ? "语音回答" : "Speak answer") : (zh ? "语音选择" : "Choose by voice"))}</button></div>
          {question.type === "text" ? <textarea className="answer-text" rows={4} value={text} onChange={(event) => setText(event.target.value)} placeholder={zh ? "可以说话，也可以输入" : "Speak or type your answer"} /> : <div className="option-grid">{question.options.map((option) => <label key={option.value} className={`big-option${selected.includes(option.value) ? " selected" : ""}`}><input type={question.type === "multi" ? "checkbox" : "radio"} name={question.id} checked={selected.includes(option.value)} onChange={() => question.type === "multi" ? setSelected(selected.includes(option.value) ? selected.filter((item) => item !== option.value) : [...selected, option.value]) : setSelected([option.value])} /><span>{option[lang]}</span></label>)}</div>}
          {error && <p className="triage-error" role="alert">{error}</p>}
          <button className="primary-button next-button" disabled={busy} onClick={() => void next()}>{busy ? (zh ? "处理中…" : "Processing…") : (zh ? "下一步" : "Next")}</button>
        </section>
      )}

      {state?.result && (
        <section className={`result-card${emergency ? " emergency-card" : ""}`} aria-live="assertive">
          {emergency ? <div className="emergency-copy"><h2>EMERGENCY</h2><p>Call 995 now.</p><p>Do not wait for this app.</p><p>Ask someone nearby to help.</p><a className="call-button" href="tel:995">☎ {zh ? "立即拨打 995" : "Call 995 now"}</a></div> : <><p className="result-level">{LEVEL[state.result.level]?.[lang] || state.result.level}</p><h2>{state.result.reason}</h2><ul>{state.result.actions.map((action) => <li key={action}>{action}</li>)}</ul></>}
          <button className="voice-button replay-result" onClick={() => speak(emergency ? "EMERGENCY. Call 995 now. Do not wait for this app. Ask someone nearby to help." : `${LEVEL[state.result!.level]?.[lang] || state.result!.level}. ${state.result!.reason}. ${state.result!.actions.join(". ")}`, lang)}>🔊 {zh ? "重新播放结果" : "Replay result"}</button>
          {mode === "caregiver" && <button className="secondary-button share-button" onClick={() => void shareResult()}>↗ {zh ? "分享给家人或陪同者" : "Share with family or helper"}</button>}
          <p className="safety-note">{state.result.disclaimer || (zh ? "这是安全分诊，不是医疗诊断。" : "This is safety triage, not a medical diagnosis.")}</p>
        </section>
      )}

      {navigation?.navigation && <section className="navigation-card"><h2>{zh ? "新加坡就医导航" : "Singapore care navigation"}</h2>{navigation.navigation.options.map((option: any) => <p key={option.id}><b>{option.name[lang]}</b>{option.phone ? ` — ${option.phone}` : ""}<br />{option.action[lang]}</p>)}</section>}
      <p className="triage-footnote">{zh ? "危急情况请先拨打 995；不要等待应用。风险等级由后端确定性规则决定。" : "Call 995 first in an emergency; do not wait for the app. Urgency is decided by deterministic backend rules."}</p>
    </main>
  );
}


