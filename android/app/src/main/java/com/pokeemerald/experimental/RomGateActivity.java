package com.pokeemerald.experimental;

import android.app.Activity;
import android.content.Intent;
import android.graphics.Color;
import android.os.Bundle;
import android.view.Gravity;
import android.widget.Button;
import android.widget.LinearLayout;
import android.widget.TextView;

import java.io.ByteArrayOutputStream;
import java.io.File;
import java.io.FileInputStream;
import java.io.FileOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.security.MessageDigest;
import java.util.Arrays;

/**
 * Restores packaged, ROM-matching data ranges using the user's own FireRed
 * Rev 1 ROM before the game starts. Debug builds without a manifest bypass
 * this gate; release builds must have a valid manifest and a verified ROM.
 */
public final class RomGateActivity extends Activity {
    private static final int PICK_ROM = 1;
    private static final int ROM_SIZE = 16 * 1024 * 1024;

    private byte[] manifest;
    private TextView status;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);

        try (InputStream in = getAssets().open("asset_manifest.bin")) {
            manifest = readFully(in);
        } catch (IOException e) {
            if (BuildConfig.DEBUG) {
                new File(getFilesDir(), "asset_manifest.bin").delete();
                launchGame();
            } else {
                showError("Missing release asset manifest. Reinstall the official release APK.");
            }
            return;
        }
        if (manifest.length < 44 || (manifest.length - 44) % 12 != 0
                || ByteBuffer.wrap(manifest, 40, 4).order(ByteOrder.LITTLE_ENDIAN).getInt()
                != (manifest.length - 44) / 12 || manifest.length == 44) {
            showError("Invalid release asset manifest. Reinstall the release APK.");
            return;
        }
        try {
            // The internal manifest must always match this exact APK.
            writeFile(new File(getFilesDir(), "asset_manifest.bin"), manifest);
        } catch (IOException e) {
            showError("Could not prepare game data: " + e.getMessage());
            return;
        }

        File internalRom = new File(getFilesDir(), "baserom.gba");
        try {
            if (internalRom.length() == ROM_SIZE
                    && validate(readFully(new FileInputStream(internalRom)))) {
                fillAndLaunch();
                return;
            }
        } catch (Exception ignored) {
            // A missing or damaged cached ROM returns to the picker.
        }

        File externalDir = getExternalFilesDir(null);
        if (externalDir != null) {
            File externalRom = new File(externalDir, "baserom.gba");
            try {
                if (externalRom.length() == ROM_SIZE) {
                    byte[] rom = readFully(new FileInputStream(externalRom));
                    if (validate(rom)) {
                        writeFile(internalRom, rom);
                        fillAndLaunch();
                        return;
                    }
                }
            } catch (Exception ignored) {
                // The document picker remains available.
            }
        }
        buildPickerUi();
    }

    private void showError(String message) {
        if (status == null) buildPickerUi();
        status.setText(message);
    }

    private void buildPickerUi() {
        LinearLayout layout = new LinearLayout(this);
        layout.setOrientation(LinearLayout.VERTICAL);
        layout.setGravity(Gravity.CENTER);
        layout.setBackgroundColor(Color.BLACK);
        status = new TextView(this);
        status.setTextColor(Color.WHITE);
        status.setTextSize(18);
        status.setGravity(Gravity.CENTER);
        status.setPadding(48, 0, 48, 32);
        status.setText("Your own Pokémon FireRed Rev 1 (USA/Europe) ROM is required.\n\n"
                + "Select the extracted 16 MiB .gba file (not a ZIP), or place it at\n"
                + "Android/data/" + getPackageName() + "/files/baserom.gba");
        Button pick = new Button(this);
        pick.setText("Select ROM");
        pick.setOnClickListener(v -> {
            Intent intent = new Intent(Intent.ACTION_OPEN_DOCUMENT);
            intent.addCategory(Intent.CATEGORY_OPENABLE);
            intent.setType("*/*");
            startActivityForResult(intent, PICK_ROM);
        });
        layout.addView(status);
        layout.addView(pick);
        setContentView(layout);
    }

    @Override
    protected void onActivityResult(int requestCode, int resultCode, Intent data) {
        super.onActivityResult(requestCode, resultCode, data);
        if (requestCode != PICK_ROM || resultCode != RESULT_OK || data == null) return;
        try {
            if (manifest == null || manifest.length < 44) {
                showError("Invalid release package. Reinstall the release APK.");
                return;
            }
            byte[] rom = readFully(getContentResolver().openInputStream(data.getData()));
            if (rom.length != ROM_SIZE) {
                showError("That file is not a 16 MiB GBA ROM. Extract ZIP files first.");
                return;
            }
            if (!validate(rom)) {
                showError("ROM hash mismatch. This build requires the exact"
                        + " USA/Europe FireRed Rev 1 ROM.");
                return;
            }
            writeFile(new File(getFilesDir(), "baserom.gba"), rom);
            fillAndLaunch();
        } catch (Exception e) {
            showError("Could not read that file: " + e.getMessage());
        }
    }

    private void fillAndLaunch() {
        try {
            System.loadLibrary("SDL2");
            System.loadLibrary("main");
            if (!DualScreenBridge.nativeFillAssets(getFilesDir().getAbsolutePath())) {
                showError("Could not restore game data. Restart the app or reinstall the release APK.");
                return;
            }
            launchGame();
        } catch (LinkageError e) {
            showError("Could not load the game libraries. This APK requires 32-bit ARM support.");
        }
    }

    private boolean validate(byte[] rom) throws Exception {
        return rom.length == ROM_SIZE && Arrays.equals(
                MessageDigest.getInstance("SHA-1").digest(rom),
                Arrays.copyOfRange(manifest, 0, 20));
    }

    private static byte[] readFully(InputStream in) throws IOException {
        if (in == null) throw new IOException("file is unavailable");
        try (InputStream stream = in) {
            ByteArrayOutputStream out = new ByteArrayOutputStream();
            byte[] buffer = new byte[65536];
            int read;
            while ((read = stream.read(buffer)) != -1) {
                if (out.size() + read > ROM_SIZE) {
                    throw new IOException("file is larger than 16 MiB");
                }
                out.write(buffer, 0, read);
            }
            return out.toByteArray();
        }
    }

    private static void writeFile(File file, byte[] data) throws IOException {
        File tmp = new File(file.getParentFile(), file.getName() + ".tmp");
        try (FileOutputStream out = new FileOutputStream(tmp)) {
            out.write(data);
        }
        if (!tmp.renameTo(file)) throw new IOException("could not finalize " + file.getName());
    }

    private void launchGame() {
        startActivity(new Intent(this, PokeEmeraldActivity.class));
        finish();
    }
}
