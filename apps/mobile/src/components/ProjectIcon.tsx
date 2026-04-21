import { StyleSheet, Text, View } from "react-native";

import { colors, radius } from "../theme/tokens";

type ProjectIconProps = {
  color: string;
  label: string;
};

export function ProjectIcon({ color, label }: ProjectIconProps) {
  return (
    <View style={[styles.icon, { backgroundColor: color }]}>
      <Text style={styles.glyph}>{label}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  icon: {
    alignItems: "center",
    borderRadius: radius.md,
    height: 68,
    justifyContent: "center",
    width: 68,
  },
  glyph: {
    color: colors.surface,
    fontSize: 30,
    fontWeight: "700",
  },
});
