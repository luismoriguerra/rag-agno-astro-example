export type AllowedPhoneNumber = {
  phone_number: string;
  created_at: string;
};

export type WhatsAppSettings = {
  enabled: boolean;
  allowed_phone_numbers: AllowedPhoneNumber[];
};

export type WhatsAppSettingsUpdate = {
  enabled: boolean;
};

export type WhatsAppAllowlistAdd = {
  phone_number: string;
};
