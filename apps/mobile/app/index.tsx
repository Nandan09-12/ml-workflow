import { LinearGradient } from "expo-linear-gradient";
import { router } from "expo-router";
import { Pressable, ScrollView, StyleSheet, Text, View } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";

import { BrandHeader } from "../src/components/BrandHeader";
import { colors, spacing, typography } from "../src/theme/tokens";

export default function SplashScreen() {
  return (
    <LinearGradient colors={["#FFFFFF", "#F7F8FB", "#EEF2FA"]} style={styles.container}>
      <SafeAreaView style={styles.safeArea}>
        <Pressable onPress={() => router.replace("/(auth)/login")} style={styles.tapTarget}>
          <ScrollView contentContainerStyle={styles.scrollContent} showsVerticalScrollIndicator={false}>
            <View style={styles.content}>
              <BrandHeader />
              <Text style={styles.helperText}>Tap anywhere to continue</Text>
            </View>
          </ScrollView>
        </Pressable>
      </SafeAreaView>
    </LinearGradient>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  safeArea: {
    flex: 1,
  },
  tapTarget: {
    flex: 1,
  scrollContent: {
    flexGrow: 1,
  },
  content: {
    alignItems: "center",
    flex: 1,
    justifyContent: "center",
    paddingHorizontal: spacing.xl,
  },
  helperText: {
    color: colors.textSecondary,
    fontSize: typography.caption,
    marginTop: spacing.xl,
  },
});
