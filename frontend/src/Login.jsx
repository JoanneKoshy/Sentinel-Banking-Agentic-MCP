import { useState } from "react";
import "./Login.css";

const AUTH_BASE = "http://127.0.0.1:8080/auth";

function Login({ onLogin }) {
  const [step, setStep] = useState("phone"); // "phone" | "otp"
  const [phoneNumber, setPhoneNumber] = useState("");
  const [otp, setOtp] = useState("");
  const [demoOtp, setDemoOtp] = useState(""); // shown on screen since SMS is simulated
  const [error, setError] = useState("");
  const [isLoading, setIsLoading] = useState(false);

  async function handleSendOtp() {
    setError("");
    if (!phoneNumber.trim()) {
      setError("Please enter your phone number.");
      return;
    }
    setIsLoading(true);
    try {
      const res = await fetch(`${AUTH_BASE}/send-otp`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ phone_number: phoneNumber.trim() }),
      });
      const data = await res.json();
      if (!res.ok) {
        setError(data.detail || "Could not send OTP.");
        return;
      }
      setDemoOtp(data.demo_otp);
      setStep("otp");
    } catch (err) {
      setError("Could not reach the server. Is the backend running?");
    } finally {
      setIsLoading(false);
    }
  }

  async function handleVerifyOtp() {
    setError("");
    if (!otp.trim()) {
      setError("Please enter the OTP.");
      return;
    }
    setIsLoading(true);
    try {
      const res = await fetch(`${AUTH_BASE}/verify-otp`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ phone_number: phoneNumber.trim(), otp: otp.trim() }),
      });
      const data = await res.json();
      if (!res.ok) {
        setError(data.detail || "Invalid OTP.");
        return;
      }
      onLogin({ token: data.token, customerId: data.customer_id, name: data.name });
    } catch (err) {
      setError("Could not reach the server. Is the backend running?");
    } finally {
      setIsLoading(false);
    }
  }

  function handleKeyDown(e, action) {
    if (e.key === "Enter") action();
  }

  return (
    <div className="login-shell">
      <div className="login-card">
        <div className="login-brand">
          <div className="brand-mark">
            <span></span><span></span><span></span><span></span>
          </div>
          <span className="brand-name">Fictional Bank</span>
        </div>

        {step === "phone" && (
          <>
            <h2>Log in to your account</h2>
            <p className="login-sub">Enter your registered phone number to receive an OTP.</p>
            <input
              type="tel"
              placeholder="Phone number"
              value={phoneNumber}
              onChange={(e) => setPhoneNumber(e.target.value)}
              onKeyDown={(e) => handleKeyDown(e, handleSendOtp)}
              disabled={isLoading}
              autoFocus
            />
            {error && <div className="login-error">{error}</div>}
            <button onClick={handleSendOtp} disabled={isLoading}>
              {isLoading ? "Sending..." : "Send OTP"}
            </button>
          </>
        )}

        {step === "otp" && (
          <>
            <h2>Enter the OTP</h2>
            <p className="login-sub">
              We sent a code to <strong>{phoneNumber}</strong>.
            </p>
            {demoOtp && (
              <div className="demo-otp-banner">
                Demo mode - SMS is simulated. Your OTP is <strong>{demoOtp}</strong>
              </div>
            )}
            <input
              type="text"
              inputMode="numeric"
              placeholder="6-digit code"
              value={otp}
              onChange={(e) => setOtp(e.target.value)}
              onKeyDown={(e) => handleKeyDown(e, handleVerifyOtp)}
              disabled={isLoading}
              maxLength={6}
              autoFocus
            />
            {error && <div className="login-error">{error}</div>}
            <button onClick={handleVerifyOtp} disabled={isLoading}>
              {isLoading ? "Verifying..." : "Verify & Login"}
            </button>
            <button
              className="link-btn"
              onClick={() => {
                setStep("phone");
                setOtp("");
                setError("");
              }}
              disabled={isLoading}
            >
              Use a different number
            </button>
          </>
        )}
      </div>
    </div>
  );
}

export default Login;