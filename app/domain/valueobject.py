from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class EmployeeId:
    """従業員IDの値オブジェクト。

    - 値は非空の文字列であること（空文字は拒否、非文字列は型エラー）
    - 典型的な値:
      - NFCタグの識別子（`identifier: bytes`）を16進大文字の連結文字列にしたもの
        例: `b"\x04\xa2\x10" -> "04A210"`
      - 任意の業務上の従業員コード（例: `"E123"`, `"YAMADA01"`）
    - バリデーション方針:
      - このクラス自身は「非空の文字列」であることのみをハードに保証します
      - フォーマット（英数字のみ、16進など）の細かな制約は上位層のユースケースや
        入力元（NFC/フォーム等）で行うことを想定しています

    シリアライズ/キー用途:
    - `str(EmployeeId)` で元の文字列を返します（CSV/JSON/辞書キーに利用可）
    """

    value: str

    def __post_init__(self) -> None:
        if not isinstance(self.value, str):
            raise TypeError("EmployeeId.value must be str")
        if self.value == "":
            raise ValueError("EmployeeId cannot be empty")

    def __str__(self) -> str:  # for CSV/JSON serialization and dict keys
        return self.value

    @classmethod
    def from_raw(cls, s: str) -> EmployeeId:
        """生の文字列から生成します。

        空文字は :class:`ValueError`、
        文字列以外は :class:`TypeError` になります（`__post_init__` により検査）。

        例:
        - `EmployeeId.from_raw("E123")`
        - `EmployeeId.from_raw("04A210")`  # 16進大文字のID
        """
        return cls(s)

    @classmethod
    def from_tag_identifier(cls, identifier: bytes) -> EmployeeId:
        """NFCタグの識別子（バイト列）から `EmployeeId` を生成します。

        - 入力: `bytes | bytearray`（`nfcpy` の `tag.identifier` など）
        - 変換: 16進表現の大文字へ変換し、区切り文字なしで連結
          例: `b"\x01\xab" -> "01AB"`
        - バリデーション: バイト列以外が渡された場合は :class:`TypeError`

        この実装はタグのUIDをそのままIDとして扱うシンプルな方針です。
        運用で別の命名規則が必要な場合は、上位のサービス層でマッピングしてください。
        """
        if not isinstance(identifier, (bytes, bytearray)):
            raise TypeError("identifier must be bytes-like")
        return cls(bytes(identifier).hex().upper())

    def to_csv(self) -> str:
        """CSV等へ出力するための文字列表現を返します。

        `str(self)` と同じで、内部の `value` をそのまま返します。
        """
        return self.value
