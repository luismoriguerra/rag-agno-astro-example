import { useCallback, useEffect, useState } from "react";

import {
  addAllowlistPhone,
  getWhatsAppSettings,
  isValidE164,
  removeAllowlistPhone,
  updateWhatsAppSettings,
} from "../services/whatsappApi";
import type { WhatsAppSettings } from "../services/whatsappTypes";

type ProfileSettingsProps = {
  userName?: string;
  userEmail?: string;
};

export default function ProfileSettings({ userName, userEmail }: ProfileSettingsProps) {
  const [settings, setSettings] = useState<WhatsAppSettings | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [phoneInput, setPhoneInput] = useState("");
  const [phoneError, setPhoneError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await getWhatsAppSettings();
      setSettings(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load settings");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  const handleToggle = async () => {
    if (!settings) return;
    setSaving(true);
    setError(null);
    try {
      const updated = await updateWhatsAppSettings({ enabled: !settings.enabled });
      setSettings(updated);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to update settings");
    } finally {
      setSaving(false);
    }
  };

  const handleAddPhone = async () => {
    const normalized = phoneInput.trim().startsWith("+")
      ? phoneInput.trim()
      : `+${phoneInput.trim().replace(/^\+/, "")}`;
    if (!isValidE164(normalized)) {
      setPhoneError("Enter a valid E.164 number (e.g. +14155552671)");
      return;
    }
    setPhoneError(null);
    setSaving(true);
    setError(null);
    try {
      const updated = await addAllowlistPhone({ phone_number: normalized });
      setSettings(updated);
      setPhoneInput("");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to add phone number");
    } finally {
      setSaving(false);
    }
  };

  const handleRemovePhone = async (phone: string) => {
    setSaving(true);
    setError(null);
    try {
      const updated = await removeAllowlistPhone(phone);
      setSettings(updated);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to remove phone number");
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="profile-shell">
      <header className="profile-header">
        <h1>Profile</h1>
        <p className="profile-user">{userName ?? "Signed-in user"}</p>
        {userEmail ? <p className="profile-email">{userEmail}</p> : null}
      </header>

      <section className="profile-section">
        <h2>WhatsApp settings</h2>
        {loading ? <p>Loading settings…</p> : null}
        {error ? <p className="profile-error">{error}</p> : null}
        {settings ? (
          <>
            <label className="toggle-row">
              <input
                type="checkbox"
                checked={settings.enabled}
                disabled={saving}
                onChange={() => void handleToggle()}
              />
              <span>Enable WhatsApp chat</span>
            </label>
            <p className="profile-hint">
              Empty allowlist = open access when enabled. Add numbers to restrict access.
            </p>
            <div className="allowlist-form">
              <input
                type="tel"
                placeholder="+14155552671"
                value={phoneInput}
                disabled={saving}
                onChange={(e) => setPhoneInput(e.target.value)}
              />
              <button type="button" disabled={saving} onClick={() => void handleAddPhone()}>
                Add phone
              </button>
            </div>
            {phoneError ? <p className="profile-error">{phoneError}</p> : null}
            <ul className="allowlist">
              {settings.allowed_phone_numbers.map((entry) => (
                <li key={entry.phone_number}>
                  <span>{entry.phone_number}</span>
                  <button
                    type="button"
                    disabled={saving}
                    onClick={() => void handleRemovePhone(entry.phone_number)}
                  >
                    Remove
                  </button>
                </li>
              ))}
            </ul>
          </>
        ) : null}
      </section>
    </div>
  );
}
