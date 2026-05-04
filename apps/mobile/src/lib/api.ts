import { Platform } from "react-native";
import { createApiClient } from "@ml-workflow/api-client";

import { getAuthSessionSnapshot } from "../auth/session";

function resolveBaseUrl(): string {
  if (Platform.OS === "ios" && process.env.EXPO_PUBLIC_API_BASE_URL_IOS) {
    return process.env.EXPO_PUBLIC_API_BASE_URL_IOS;
  }

  if (Platform.OS === "android" && process.env.EXPO_PUBLIC_API_BASE_URL_ANDROID) {
    return process.env.EXPO_PUBLIC_API_BASE_URL_ANDROID;
  }

  return process.env.EXPO_PUBLIC_API_BASE_URL ?? "http://localhost:8000";
}

export const apiClient = createApiClient({
  baseUrl: resolveBaseUrl(),
  getAccessToken: () => getAuthSessionSnapshot().accessToken,
});
