import { LinearGradient } from "expo-linear-gradient";
import { router } from "expo-router";
import { useEffect, useState } from "react";
import { Controller, useForm } from "react-hook-form";
import { Pressable, StyleSheet, Switch, Text, TextInput, View } from "react-native";
import { z } from "zod";
import { zodResolver } from "@hookform/resolvers/zod";

import { useAuth } from "../../src/auth/AuthContext";
import { BrandHeader } from "../../src/components/BrandHeader";
import { PrimaryButton } from "../../src/components/PrimaryButton";
import { colors, radius, spacing, typography } from "../../src/theme/tokens";

const loginSchema = z.object({
  email: z.string().email("Enter a valid email address"),
  password: z.string().min(6, "Enter your password"),
  rememberMe: z.boolean(),
});

type LoginForm = z.infer<typeof loginSchema>;

export default function LoginScreen() {
  const [isPasswordVisible, setIsPasswordVisible] = useState(false);
  const {
    clearError,
    errorMessage,
    isSubmitting,
    signInWithPassword,
  } = useAuth();
  const showMicrosoftSignIn = true;
  const {
    control,
    formState: { errors },
    handleSubmit,
  } = useForm<LoginForm>({
    defaultValues: {
      email: "",
      password: "",
      rememberMe: true,
    },
    resolver: zodResolver(loginSchema),
  });

  useEffect(() => {
    clearError();
  }, []);

  const onSubmit = async (values: LoginForm) => {
    const result = await signInWithPassword(values);

    if (result === "APPROVED") {
      router.replace("/(tabs)/projects");
      return;
    }

    if (result === "PENDING_APPROVAL") {
      router.replace("/pending-approval");
    }
  };

  const goToRegister = () => {
    clearError();
    router.replace("/(auth)/register");
  };

  const goToMicrosoftLogin = () => {
    clearError();
    router.push("/(auth)/microsoft-login");
  };

  return (
    <LinearGradient colors={["#EEF2FA", "#D8DBF0", "#8F83B9"]} style={styles.container}>
      <View style={styles.safeArea}>
        <View style={styles.header}>
          <BrandHeader />
        </View>

        <View style={styles.card}>
          <Text style={styles.heading}>Log in</Text>
          <Text style={styles.subheading}>with your ML Technologies account</Text>

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
                {errors.email ? <Text style={styles.errorText}>{errors.email.message}</Text> : null}
              </View>
            )}
          />

          <Controller
            control={control}
            name="password"
            render={({ field: { onChange, value } }) => (
              <View style={styles.fieldBlock}>
                <View style={styles.passwordRow}>
                  <TextInput
                    onChangeText={onChange}
                    placeholder="Enter password"
                    placeholderTextColor="#9699A8"
                    secureTextEntry={!isPasswordVisible}
                    style={styles.passwordInput}
                    value={value}
                  />
                  <Pressable
                    onPress={() => setIsPasswordVisible((current) => !current)}
                    style={styles.passwordToggle}
                  >
                    <Text style={styles.passwordToggleText}>
                      {isPasswordVisible ? "HIDE" : "SHOW"}
                    </Text>
                  </Pressable>
                </View>
                {errors.password ? (
                  <Text style={styles.errorText}>{errors.password.message}</Text>
                ) : null}
              </View>
            )}
          />

          <Controller
            control={control}
            name="rememberMe"
            render={({ field: { onChange, value } }) => (
              <View style={styles.rememberRow}>
                <Switch
                  onValueChange={onChange}
                  thumbColor={colors.surface}
                  trackColor={{ false: "#C6CAD9", true: colors.brandSoft }}
                  value={value}
                />
                <Text style={styles.rememberText}>Remember me</Text>
              </View>
            )}
          />

          {errorMessage ? <Text style={styles.errorBanner}>{errorMessage}</Text> : null}

          <PrimaryButton
            label={isSubmitting ? "SIGNING IN..." : "LOG IN"}
            onPress={handleSubmit(onSubmit)}
          />

          {showMicrosoftSignIn ? (
            <>
              <Text style={styles.dividerText}>OR</Text>
              <Pressable onPress={goToMicrosoftLogin} style={styles.microsoftButton}>
                <Text style={styles.microsoftLabel}>CONTINUE WITH MICROSOFT</Text>
              </Pressable>
            </>
          ) : (
            <Text style={styles.helperText}>
              Microsoft sign-in will be added after email/password login is fully stabilized.
            </Text>
          )}

          <View style={styles.registerRow}>
            <Text style={styles.registerText}>Don't have an account?</Text>
            <Pressable onPress={goToRegister}>
              <Text style={styles.registerLink}>Register here</Text>
            </Pressable>
          </View>
        </View>

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
  passwordRow: {
    alignItems: "center",
    borderBottomColor: "#B7BCCA",
    borderBottomWidth: 1,
    flexDirection: "row",
    minHeight: 50,
  },
  passwordInput: {
    color: colors.textPrimary,
    flex: 1,
    fontSize: typography.body,
    minHeight: 50,
  },
  passwordToggle: {
    alignItems: "center",
    justifyContent: "center",
    paddingHorizontal: spacing.sm,
  },
  passwordToggleText: {
    color: colors.brandSoft,
    fontSize: typography.caption,
    fontWeight: "700",
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
  rememberRow: {
    alignItems: "center",
    flexDirection: "row",
    gap: spacing.sm,
    marginBottom: spacing.lg,
  },
  rememberText: {
    color: colors.textPrimary,
    fontSize: typography.body,
  },
  dividerText: {
    color: colors.textSecondary,
    fontSize: typography.body,
    marginVertical: spacing.md,
    textAlign: "center",
  },
  helperText: {
    color: colors.textSecondary,
    fontSize: typography.caption,
    lineHeight: 18,
    marginTop: spacing.lg,
    textAlign: "center",
  },
  microsoftButton: {
    alignItems: "center",
    borderColor: "#A9AFBE",
    borderRadius: radius.sm,
    borderWidth: 1,
    justifyContent: "center",
    minHeight: 52,
  },
  microsoftLabel: {
    color: "#777D8F",
    fontSize: 15,
    fontWeight: "500",
  },
  registerRow: {
    alignItems: "center",
    flexDirection: "row",
    gap: spacing.xs,
    justifyContent: "center",
    marginTop: spacing.lg,
  },
  registerText: {
    color: colors.textSecondary,
    fontSize: typography.body,
  },
  registerLink: {
    color: colors.brandSoft,
    fontSize: typography.body,
    fontWeight: "600",
  },
  termsText: {
    color: "#F4F4FA",
    fontSize: typography.caption,
    lineHeight: 18,
    marginTop: spacing.lg,
    paddingHorizontal: spacing.md,
    textAlign: "center",
  },
});
