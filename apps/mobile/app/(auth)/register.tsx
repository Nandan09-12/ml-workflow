import { LinearGradient } from "expo-linear-gradient";
import { router } from "expo-router";
import { useEffect, useState } from "react";
import { Controller, useForm } from "react-hook-form";
import { Pressable, ScrollView, StyleSheet, Text, TextInput, View } from "react-native";
import { z } from "zod";
import { zodResolver } from "@hookform/resolvers/zod";

import { useAuth } from "../../src/auth/AuthContext";
import { BrandHeader } from "../../src/components/BrandHeader";
import { PrimaryButton } from "../../src/components/PrimaryButton";
import { colors, radius, spacing, typography } from "../../src/theme/tokens";

const registerSchema = z
  .object({
    name: z
      .string()
      .min(2, "Name must be at least 2 characters")
      .max(50, "Name must not exceed 50 characters")
      .regex(/^[a-zA-Z\s]*$/, "Name can only contain letters and spaces"),
    email: z.string().email("Enter a valid email address"),
    phoneNumber: z
      .string()
      .regex(/^\+?[0-9]{10,}$/, "Enter a valid phone number (at least 10 digits)"),
    password: z
      .string()
      .min(8, "Password must be at least 8 characters")
      .regex(/[A-Z]/, "Password must contain at least one uppercase letter")
      .regex(/[0-9]/, "Password must contain at least one number")
      .regex(/[!@#$%^&*]/, "Password must contain at least one special character (!@#$%^&*)"),
    confirmPassword: z.string(),
  })
  .refine((data) => data.password === data.confirmPassword, {
    message: "Passwords do not match",
    path: ["confirmPassword"],
  });

type RegisterForm = z.infer<typeof registerSchema>;

export default function RegisterScreen() {
  const { clearError, errorMessage, isSubmitting, signUpWithPassword } = useAuth();
  const {
    control,
    formState: { errors },
    handleSubmit,
    reset,
    watch,
  } = useForm<RegisterForm>({
    defaultValues: {
      name: "",
      email: "",
      phoneNumber: "",
      password: "",
      confirmPassword: "",
    },
    resolver: zodResolver(registerSchema),
  });

  const password = watch("password");
  const [submittedEmail, setSubmittedEmail] = useState<string | null>(null);
  const isConfirmationNotice =
    errorMessage === "Account created. Check your email to confirm it, then log in.";

  useEffect(() => {
    clearError();
  }, [clearError]);

  const onSubmit = async (values: RegisterForm) => {
    const payload = {
      name: values.name.trim(),
      email: values.email.trim(),
      phoneNumber: values.phoneNumber.trim(),
      password: values.password,
    };

    setSubmittedEmail(payload.email);
    const didSignUp = await signUpWithPassword(payload);

    if (didSignUp) {
      router.replace("/(tabs)/projects");
      return;
    }

    if (errorMessage !== "Account created. Check your email to confirm it, then log in.") {
      setSubmittedEmail(null);
    }
  };

  return (
    <LinearGradient colors={["#EEF2FA", "#D8DBF0", "#8F83B9"]} style={styles.container}>
      <View style={styles.safeArea}>
        <View style={styles.header}>
          <BrandHeader />
        </View>

        <ScrollView
          contentContainerStyle={styles.scrollContent}
          keyboardShouldPersistTaps="handled"
          showsVerticalScrollIndicator={false}
        >
          <View style={styles.card}>
            {isConfirmationNotice ? (
              <>
                <Text style={styles.heading}>Account Created</Text>
                <Text style={styles.subheading}>Check your email to continue</Text>
                <View style={styles.successCard}>
                  <Text style={styles.successTitle}>Confirm your email</Text>
                  <Text style={styles.successBody}>
                    {submittedEmail ?? "Your account"} has been created. Open the confirmation email,
                    verify your address, then come back here to log in.
                  </Text>
                </View>
                <Pressable
                  onPress={() => {
                    clearError();
                    setSubmittedEmail(null);
                    reset();
                    router.replace("/(auth)/login");
                  }}
                  style={styles.secondaryButton}
                >
                  <Text style={styles.secondaryButtonText}>GO TO LOGIN</Text>
                </Pressable>
              </>
            ) : (
              <>
                <Text style={styles.heading}>Create Account</Text>
                <Text style={styles.subheading}>with ML Technologies</Text>

                <Controller
                  control={control}
                  name="name"
                  render={({ field: { onChange, value } }) => (
                    <View style={styles.fieldBlock}>
                      <TextInput
                        autoCapitalize="words"
                        onChangeText={onChange}
                        placeholder="Enter your name"
                        placeholderTextColor="#9699A8"
                        style={styles.input}
                        value={value}
                      />
                      {errors.name ? (
                        <Text style={styles.errorText}>{errors.name.message}</Text>
                      ) : null}
                    </View>
                  )}
                />

                <Controller
                  control={control}
                  name="email"
                  render={({ field: { onChange, value } }) => (
                    <View style={styles.fieldBlock}>
                      <TextInput
                        autoCapitalize="none"
                        keyboardType="email-address"
                        onChangeText={onChange}
                        placeholder="Enter email address"
                        placeholderTextColor="#9699A8"
                        style={styles.input}
                        value={value}
                      />
                      {errors.email ? (
                        <Text style={styles.errorText}>{errors.email.message}</Text>
                      ) : null}
                    </View>
                  )}
                />

                <Controller
                  control={control}
                  name="phoneNumber"
                  render={({ field: { onChange, value } }) => (
                    <View style={styles.fieldBlock}>
                      <TextInput
                        keyboardType="phone-pad"
                        onChangeText={onChange}
                        placeholder="Enter phone number"
                        placeholderTextColor="#9699A8"
                        style={styles.input}
                        value={value}
                      />
                      {errors.phoneNumber ? (
                        <Text style={styles.errorText}>{errors.phoneNumber.message}</Text>
                      ) : null}
                    </View>
                  )}
                />

                <Controller
                  control={control}
                  name="password"
                  render={({ field: { onChange, value } }) => (
                    <View style={styles.fieldBlock}>
                      <TextInput
                        onChangeText={onChange}
                        placeholder="Enter password"
                        placeholderTextColor="#9699A8"
                        secureTextEntry
                        style={styles.input}
                        value={value}
                      />
                      {errors.password ? (
                        <Text style={styles.errorText}>{errors.password.message}</Text>
                      ) : null}
                      {value && !errors.password && (
                        <Text style={styles.successText}>Password meets requirements</Text>
                      )}
                    </View>
                  )}
                />

                <Controller
                  control={control}
                  name="confirmPassword"
                  render={({ field: { onChange, value } }) => (
                    <View style={styles.fieldBlock}>
                      <TextInput
                        onChangeText={onChange}
                        placeholder="Confirm password"
                        placeholderTextColor="#9699A8"
                        secureTextEntry
                        style={styles.input}
                        value={value}
                      />
                      {errors.confirmPassword ? (
                        <Text style={styles.errorText}>{errors.confirmPassword.message}</Text>
                      ) : null}
                      {value && password && value === password && !errors.confirmPassword && (
                        <Text style={styles.successText}>Passwords match</Text>
                      )}
                    </View>
                  )}
                />

                {errorMessage ? <Text style={styles.errorBanner}>{errorMessage}</Text> : null}

                <PrimaryButton
                  label={isSubmitting ? "CREATING ACCOUNT..." : "REGISTER"}
                  onPress={handleSubmit(onSubmit)}
                />

                <View style={styles.loginRow}>
                  <Text style={styles.loginText}>Already have an account?</Text>
                  <Pressable onPress={() => router.replace("/(auth)/login")}>
                    <Text style={styles.loginLink}>Log in</Text>
                  </Pressable>
                </View>
              </>
            )}
          </View>
        </ScrollView>

        <Text style={styles.termsText}>
          By proceeding, you agree to the Terms of Service and Privacy Policy.
        </Text>
      </View>
    </LinearGradient>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  safeArea: {
    flex: 1,
    paddingHorizontal: spacing.md,
    paddingTop: spacing.xl,
  },
  scrollContent: {
    flexGrow: 1,
  },
  header: {
    paddingBottom: spacing.lg,
    paddingTop: spacing.sm,
  },
  card: {
    backgroundColor: colors.surface,
    borderRadius: radius.md,
    paddingHorizontal: spacing.lg,
    paddingVertical: spacing.xl,
    shadowColor: "#141831",
    shadowOffset: { width: 0, height: 10 },
    shadowOpacity: 0.12,
    shadowRadius: 18,
  },
  heading: {
    color: colors.textPrimary,
    fontSize: 24,
    fontWeight: "800",
    textAlign: "center",
  },
  subheading: {
    color: colors.textSecondary,
    fontSize: typography.body,
    marginBottom: spacing.lg,
    marginTop: spacing.xs,
    textAlign: "center",
  },
  fieldBlock: {
    marginBottom: spacing.md,
  },
  input: {
    borderBottomColor: "#B7BCCA",
    borderBottomWidth: 1,
    color: colors.textPrimary,
    fontSize: typography.body,
    minHeight: 50,
  },
  errorText: {
    color: "#C43F5A",
    fontSize: typography.caption,
    marginTop: spacing.xs,
  },
  errorBanner: {
    color: "#C43F5A",
    fontSize: typography.caption,
    marginBottom: spacing.md,
  },
  successCard: {
    backgroundColor: "#F4F8F4",
    borderColor: "#D4E8D7",
    borderRadius: radius.sm,
    borderWidth: 1,
    marginBottom: spacing.lg,
    padding: spacing.md,
  },
  successTitle: {
    color: colors.textPrimary,
    fontSize: typography.body,
    fontWeight: "700",
    marginBottom: spacing.xs,
  },
  successBody: {
    color: colors.textSecondary,
    fontSize: typography.body,
    lineHeight: 24,
  },
  secondaryButton: {
    alignItems: "center",
    borderColor: "#A9AFBE",
    borderRadius: radius.sm,
    borderWidth: 1,
    justifyContent: "center",
    marginBottom: spacing.md,
    minHeight: 52,
  },
  secondaryButtonText: {
    color: colors.textPrimary,
    fontSize: 15,
    fontWeight: "600",
  },
  successText: {
    color: "#4CAF50",
    fontSize: typography.caption,
    marginTop: spacing.xs,
  },
  loginRow: {
    alignItems: "center",
    flexDirection: "row",
    gap: spacing.xs,
    justifyContent: "center",
    marginTop: spacing.lg,
  },
  loginText: {
    color: colors.textSecondary,
    fontSize: typography.body,
  },
  loginLink: {
    color: colors.brandSoft,
    fontSize: typography.body,
    fontWeight: "600",
  },
  termsText: {
    color: "#F4F4FA",
    fontSize: typography.caption,
    lineHeight: 18,
    marginTop: spacing.lg,
    marginBottom: spacing.lg,
    paddingHorizontal: spacing.md,
    textAlign: "center",
  },
});
