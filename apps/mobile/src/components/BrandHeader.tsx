import { StyleSheet, Text, View } from "react-native";

import { LogoMark } from "./LogoMark";
import { colors } from "../theme/tokens";

export function BrandHeader() {
  return (
    <View style={styles.container}>
      <LogoMark />
      <View style={styles.copy}>
        <Text style={styles.title}>ML Technologies</Text>
        <Text style={styles.title}>Workforce</Text>
        <Text style={styles.title}>Management</Text>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    alignItems: "flex-start",
    flexDirection: "row",
    gap: 12,
  },
  copy: {
    flexShrink: 1,
    gap: 2,
    paddingTop: 4,
  },
  title: {
    color: colors.textPrimary,
    fontSize: 21,
    fontWeight: "800",
    lineHeight: 25,
  },
});
