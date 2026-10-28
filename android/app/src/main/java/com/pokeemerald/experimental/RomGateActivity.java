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
                showError("Sürüm varlık bildirimi eksik. Resmi sürüm APK'sını yeniden yükleyin.");
            }
            return;
        }
        if (manifest.length < 44 || (manifest.length - 44) % 12 != 0
                || ByteBuffer.wrap(manifest, 40, 4).order(ByteOrder.LITTLE_ENDIAN).getInt()
                != (manifest.length - 44) / 12 || manifest.length == 44) {
            showError("Geçersiz sürüm varlık bildirimi. Sürüm APK'sını yeniden yükleyin.");
            return;
        }
        try {
            // The internal manifest must always match this exact APK.
            writeFile(new File(getFilesDir(), "asset_manifest.bin"), manifest);
        } catch (IOException e) {
            showError("Oyun verileri hazırlanamadı: " + e.getMessage());
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
        status.setText("Kendi Pokémon FireRed Rev 1 (ABD/Avrupa) ROM dosyanız gerekiyor.\n\n"
                + "Çıkarılmış 16 MiB .gba dosyasını seçin (ZIP değil) ya da şuraya koyun:\n"
                + "Android/data/" + getPackageName() + "/files/baserom.gba");
        Button pick = new Button(this);
        pick.setText("ROM Seç");
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
                showError("Geçersiz sürüm paketi. Sürüm APK'sını yeniden yükleyin.");
                return;
            }
            byte[] rom = readFully(getContentResolver().openInputStream(data.getData()));
            if (rom.length != ROM_SIZE) {
                showError("Bu dosya 16 MiB GBA ROM değil. Önce ZIP dosyalarını çıkarın.");
                return;
            }
            if (!validate(rom)) {
                showError("ROM özeti uyuşmuyor. Bu sürüm tam olarak"
                        + " ABD/Avrupa FireRed Rev 1 ROM'unu gerektirir.");
                return;
            }
            writeFile(new File(getFilesDir(), "baserom.gba"), rom);
            fillAndLaunch();
        } catch (Exception e) {
            showError("Dosya okunamadı: " + e.getMessage());
        }
    }

    private void fillAndLaunch() {
        try {
            System.loadLibrary("SDL2");
            System.loadLibrary("main");
            if (!DualScreenBridge.nativeFillAssets(getFilesDir().getAbsolutePath())) {
                showError("Oyun verileri geri yüklenemedi. Uygulamayı yeniden başlatın ya da sürüm APK'sını yeniden yükleyin.");
                return;
            }
            launchGame();
        } catch (LinkageError e) {
            showError("Oyun kütüphaneleri yüklenemedi. Bu APK 32 bit ARM desteği gerektirir.");
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
