import { LinearGradient } from "expo-linear-gradient";
import { router } from "expo-router";
import { useEffect, useState } from "react";
import { Controller, useForm } from "react-hook-form";
import { Modal, Pressable, ScrollView, StyleSheet, Text, TextInput, View } from "react-native";
import { z } from "zod";
import { zodResolver } from "@hookform/resolvers/zod";

import { useAuth } from "../../src/auth/AuthContext";
import { BackButton } from "../../src/components/BackButton";
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

type RegistrationModalState =
  | { kind: "EMAIL_ALREADY_USED"; email: string }
  | { kind: "VERIFY_EMAIL_REQUIRED"; email: string }
  | null;

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
  const [registrationModal, setRegistrationModal] = useState<RegistrationModalState>(null);

  useEffect(() => {
    clearError();
  }, [clearError]);

  const closeRegistrationModal = () => {
    setRegistrationModal(null);
  };

  const goToLogin = () => {
    clearError();
    setRegistrationModal(null);
    router.replace("/(auth)/login");
  };

  const onSubmit = async (values: RegisterForm) => {
    const payload = {
      name: values.name.trim(),
      email: values.email.trim(),
      phoneNumber: values.phoneNumber.trim(),
      password: values.password,
    };

    const signUpResult = await signUpWithPassword(payload);

    if (signUpResult === true) {
      setRegistrationModal(null);
      router.replace("/(tabs)/projects");
      return;
    }

    if (signUpResult === "EMAIL_ALREADY_USED") {
      setRegistrationModal({
        kind: "EMAIL_ALREADY_USED",
        email: payload.email,
      });
      return;
    }

    if (signUpResult === "VERIFY_EMAIL_REQUIRED") {
      reset();
      setRegistrationModal({
        kind: "VERIFY_EMAIL_REQUIRED",
        email: payload.email,
      });
      return;
    }

    setRegistrationModal(null);
  };

  return (
    <LinearGradient colors={["#EEF2FA", "#D8DBF0", "#8F83B9"]} style={styles.container}>
      <View style={styles.safeArea}>
        <View style={styles.navRow}>
          <BackButton fallbackHref="/(auth)/login" />
        </View>
        <View style={styles.header}>
          <BrandHeader />
        </View>

        <ScrollView
          contentContainerStyle={styles.scrollContent}
          keyboardShouldPersistTaps="handled"
          showsVerticalScrollIndicator={false}
        >
          <View style={styles.card}>
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
              <Pressable onPress={goToLogin}>
                <Text style={styles.loginLink}>Log in</Text>
              </Pressable>
            </View>
          </View>
        </ScrollView>

        <Text style={styles.termsText}>
          By proceeding, you agree to the Terms of Service and Privacy Policy.
        </Text>
      </View>

      <Modal
        animationType="fade"
        onRequestClose={closeRegistrationModal}
        transparent
        visible={registrationModal !== null}
      >
        <View style={styles.modalBackdrop}>
          <View style={styles.modalCard}>
            <Text style={styles.modalTitle}>
              {registrationModal?.kind === "EMAIL_ALREADY_USED"
                ? "Email already used"
                : "Verification email sent!"}
            </Text>

            {registrationModal?.kind === "EMAIL_ALREADY_USED" ? (
              <Text style={styles.modalBody}>
                {registrationModal.email} is already used. Please log in or use another email
                address.
              </Text>
            ) : (
              <Text style={styles.modalBody}>
                We sent a verification email to {registrationModal?.email}. Please verify your email,
                then{" "}
                <Text onPress={goToLogin} style={styles.modalLink}>
                  Login here
                </Text>
                .
              </Text>
            )}

            <Pressable onPress={closeRegistrationModal} style={styles.modalButton}>
              <Text style={styles.modalButtonText}>
                {registrationModal?.kind === "EMAIL_ALREADY_USED" ? "OK" : "CLOSE"}
              </Text>
            </Pressable>
          </View>
        </View>
      </Modal>
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
  navRow: {
    paddingTop: spacing.xs,
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
  modalBackdrop: {
    alignItems: "center",
    backgroundColor: "rgba(20, 24, 49, 0.45)",
    flex: 1,
    justifyContent: "center",
    paddingHorizontal: spacing.lg,
  },
  modalCard: {
    backgroundColor: colors.surface,
    borderRadius: radius.md,
    maxWidth: 420,
    padding: spacing.lg,
    shadowColor: "#141831",
    shadowOffset: { width: 0, height: 12 },
    shadowOpacity: 0.2,
    shadowRadius: 20,
    width: "100%",
  },
  modalTitle: {
    color: colors.textPrimary,
    fontSize: 22,
    fontWeight: "800",
    marginBottom: spacing.sm,
    textAlign: "center",
  },
  modalBody: {
    color: colors.textSecondary,
    fontSize: typography.body,
    lineHeight: 24,
    marginBottom: spacing.lg,
    textAlign: "center",
  },
  modalLink: {
    color: colors.brandSoft,
    fontSize: typography.body,
    fontWeight: "700",
    textDecorationLine: "underline",
  },
  modalButton: {
    alignItems: "center",
    borderColor: "#A9AFBE",
    borderRadius: radius.sm,
    borderWidth: 1,
    justifyContent: "center",
    minHeight: 52,
  },
  modalButtonText: {
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
