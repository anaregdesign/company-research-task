from __future__ import annotations

from typing import List, Optional, Literal
from pydantic import BaseModel, Field
from openaivec import PreparedTask


# ========== 補助モデル（Dictを避けるためのKV配列） ==========
class SegmentRatio(BaseModel):
    name: str = Field(..., description="セグメント名")
    ratio: float = Field(..., ge=0.0, le=1.0, description="売上構成比（0〜1）")


class SegmentAmount(BaseModel):
    name: str = Field(..., description="セグメント名")
    amount_yen: float = Field(..., ge=0.0, description="売上高（円）")


# ========== FiscalPeriod ==========
class FiscalPeriod(BaseModel):
    period_type: Literal["annual", "quarter"] = Field(..., description="会計期間の種類。")
    fiscal_year: int = Field(
        ..., ge=1900, le=2100,
        description="会計年度 (例: 2025)。FY25は通常2024-04-01〜2025-03-31（3月期決算の場合）。"
    )
    quarter: Optional[Literal[1, 2, 3, 4]] = Field(
        None,
        description="四半期 (1〜4)。例: FY25 Q1 = 2024-04-01〜2024-06-30。年次のみは None。"
    )
    period_start: Optional[str] = Field(None, description="期間開始日（YYYY-MM-DD 文字列）")
    period_end: Optional[str] = Field(None, description="期間終了日（YYYY-MM-DD 文字列）")


# ========== 1) 企業基礎 ==========
class Executive(BaseModel):
    name: str = Field(..., description="役員氏名（フルネーム）")
    title: str = Field(..., description="役職（例: 代表取締役社長、取締役CIO 等）")
    career_summary: Optional[str] = Field(None, description="略歴。学歴・職歴・過去の役職などを自由記述形式でまとめる。")
    responsibility: Optional[str] = Field(None, description="担当範囲。経営企画、IT戦略、研究開発、人事などの主要な管掌領域。")
    start_date: Optional[str] = Field(None, description="着任日（YYYY-MM-DD）")
    end_date: Optional[str] = Field(None, description="退任日（YYYY-MM-DD）")
    source_url: Optional[str] = Field(None, description="役員情報の根拠URL")


class CompanyBasic(BaseModel):
    company_name: str = Field(..., description="商号（正式名）")
    ticker_code: Optional[int] = Field(None, ge=1000, le=9999, description="証券コード（4桁。非上場はNone）")
    market: Optional[Literal["Prime", "Standard", "Growth", "Non-listed"]] = Field(None, description="市場区分")
    corporate_number: Optional[str] = Field(None, description="法人番号（13桁）")
    # 変更: 本社所在地を都道府県Literalで強制
    headquarters_pref: Optional[Literal[
        "北海道","青森県","岩手県","宮城県","秋田県","山形県","福島県",
        "茨城県","栃木県","群馬県","埼玉県","千葉県","東京都","神奈川県",
        "新潟県","富山県","石川県","福井県","山梨県","長野県","岐阜県",
        "静岡県","愛知県","三重県","滋賀県","京都府","大阪府","兵庫県",
        "奈良県","和歌山県","鳥取県","島根県","岡山県","広島県","山口県",
        "徳島県","香川県","愛媛県","高知県","福岡県","佐賀県","長崎県",
        "熊本県","大分県","宮崎県","鹿児島県","沖縄県"
    ]] = Field(None, description="本社所在地（都道府県）")
    founded_year: Optional[int] = Field(None, ge=1600, le=2100, description="設立年")
    capital_yen: Optional[int] = Field(None, ge=0, description="資本金（円）")
    employees_consolidated: Optional[int] = Field(None, ge=0, description="従業員数（連結）")
    executives: List[Executive] = Field(default_factory=list, description="主要役員")
    accounting_standard: Optional[Literal["JGAAP", "IFRS", "USGAAP"]] = Field(None, description="会計基準")
    fiscal_year_start_month: Optional[int] = Field(None, ge=1, le=12, description="期首月（例: 4=4月）")
    source_url: Optional[str] = Field(None, description="会社概要の根拠URL")


# ========== 2) 財務 ==========
class FinancialRecord(BaseModel):
    period: FiscalPeriod = Field(..., description="会計期間（FY・四半期）")
    is_consolidated: Optional[bool] = Field(True, description="連結かどうか（通常 True）")
    is_cumulative: Optional[bool] = Field(True, description="累計(YTD)か単期か")
    restated: Optional[bool] = Field(False, description="組替え・遡及修正の有無")

    # --- PL ---
    revenue_yen: Optional[float] = Field(None, ge=0, description="売上高（円）")
    op_income_yen: Optional[float] = Field(None, ge=0, description="営業利益（円）")
    ordinary_income_yen: Optional[float] = Field(None, ge=0, description="経常利益（円）")
    ebitda_yen: Optional[float] = Field(None, ge=0, description="EBITDA（円）")
    net_income_yen: Optional[float] = Field(None, ge=0, description="当期純利益（円）")
    eps_yen: Optional[float] = Field(None, ge=0, description="EPS（円）")

    # --- BS ---
    total_assets_yen: Optional[float] = Field(None, ge=0, description="総資産（円）")
    net_assets_yen: Optional[float] = Field(None, ge=0, description="純資産（円）")
    equity_ratio: Optional[float] = Field(None, ge=0.0, le=1.0, description="自己資本比率（0〜1）")
    interest_bearing_debt_yen: Optional[float] = Field(None, ge=0, description="有利子負債（円）")
    roe: Optional[float] = Field(None, ge=-1.0, le=1.0, description="ROE（0〜1のfloat、負値可。%表記からは0-1に変換）")
    roa: Optional[float] = Field(None, ge=-1.0, le=1.0, description="ROA（0〜1のfloat、負値可。%表記からは0-1に変換）")

    # --- セグメント（Dict禁止→配列へ） ---
    segment_revenue_ratio: List[SegmentRatio] = Field(
        default_factory=list, description="セグメント別の売上構成比（0〜1）の配列"
    )
    segment_revenue_yen: List[SegmentAmount] = Field(
        default_factory=list, description="セグメント別の売上高（円）の配列"
    )

    notes: Optional[str] = Field(None, description="補足（IFRS移行、特殊要因など）")
    source_url: Optional[str] = Field(None, description="財務データの根拠URL")


class Financials(BaseModel):
    records: List[FinancialRecord] = Field(default_factory=list, description="直近3年程度の財務レコード")
    source_url: Optional[str] = Field(None, description="財務情報全体の参照URL")
    last_verified_at: Optional[str] = Field(None, description="最終検証日（YYYY-MM-DD）")


# ========== 3) 人事・組織 ==========
class OrgSignal(BaseModel):
    event_type: Optional[Literal["EXECUTIVE_CHANGE", "DEPT_CREATED", "DX_APPOINTMENT", "OTHER"]] = Field(
        None, description="イベント種別"
    )
    title: str = Field(..., description="イベント概要")
    announced_date: Optional[str] = Field(None, description="発表日（YYYY-MM-DD）")
    source_url: Optional[str] = Field(None, description="根拠URL")


# ========== 4) 広報・SNS ==========
class SocialAccount(BaseModel):
    platform: Literal["X", "LinkedIn", "Instagram", "YouTube", "Facebook", "TikTok", "Other"] = Field(
        ..., description="SNS種別"
    )
    url: str = Field(..., description="アカウントURL（文字列）")
    handle: Optional[str] = Field(None, description="@handle")
    followers: Optional[int] = Field(None, ge=0, description="フォロワー数")
    last_post_date: Optional[str] = Field(None, description="最終投稿日（YYYY-MM-DD）")
    active: Optional[bool] = Field(None, description="直近運用中か")
    source_url: Optional[str] = Field(None, description="根拠URL")


class Communications(BaseModel):
    owned_media_urls: List[str] = Field(default_factory=list, description="コーポレート/IR等の主要URL（文字列）")
    social_accounts: List[SocialAccount] = Field(default_factory=list, description="運用SNSアカウント")
    source_url: Optional[str] = Field(None, description="広報情報の根拠URL")
    last_verified_at: Optional[str] = Field(None, description="検証日（YYYY-MM-DD）")


# ========== 5) 競合 ==========
class Competitor(BaseModel):
    name: str = Field(..., description="競合企業名")
    areas: List[str] = Field(default_factory=list, description="競合領域（例: EC, 決済, 広告）")
    notes: Optional[str] = Field(None, description="競合領域に関する解説")
    source_url: Optional[str] = Field(None, description="根拠URL")


# 新規: グループ会社・子会社モデル（上場/非上場どちらも扱う）
class GroupCompany(BaseModel):
    name: str = Field(..., description="グループ会社・子会社の社名（正式名）")
    relation_type: Optional[Literal["subsidiary", "affiliate", "joint_venture", "other"]] = Field(
        None, description="対対象企業との関係（subsidiary=子会社, affiliate=関連会社, joint_venture=JV, other=その他）"
    )
    ownership_ratio: Optional[float] = Field(None, ge=0.0, le=1.0, description="持株比率（0〜1）")
    is_listed: Optional[bool] = Field(None, description="上場の有無（True=上場, False=非上場, None=不明）")
    ticker_code: Optional[int] = Field(None, ge=1000, le=9999, description="証券コード（4桁。上場でない場合はNone）")
    market: Optional[Literal["Prime", "Standard", "Growth", "Non-listed"]] = Field(None, description="市場区分")
    corporate_number: Optional[str] = Field(None, description="法人番号（13桁）")
    # 変更: 本社所在地を都道府県Literalで強制
    headquarters_pref: Optional[Literal[
        "北海道","青森県","岩手県","宮城県","秋田県","山形県","福島県",
        "茨城県","栃木県","群馬県","埼玉県","千葉県","東京都","神奈川県",
        "新潟県","富山県","石川県","福井県","山梨県","長野県","岐阜県",
        "静岡県","愛知県","三重県","滋賀県","京都府","大阪府","兵庫県",
        "奈良県","和歌山県","鳥取県","島根県","岡山県","広島県","山口県",
        "徳島県","香川県","愛媛県","高知県","福岡県","佐賀県","長崎県",
        "熊本県","大分県","宮崎県","鹿児島県","沖縄県"
    ]] = Field(None, description="本社所在地（都道府県、Literalで固定）")
    founded_year: Optional[int] = Field(None, ge=1600, le=2100, description="設立年")
    capital_yen: Optional[int] = Field(None, ge=0, description="資本金（円）")
    employees: Optional[int] = Field(None, ge=0, description="従業員数（単体）")
    business_summary: Optional[str] = Field(None, description="事業内容の要約")
    notes: Optional[str] = Field(None, description="補足（持株構成、主要顧客、事業統合状況など）")
    source_url: Optional[str] = Field(None, description="グループ会社情報の根拠URL（会社HP/会社案内/登記情報等）")


# ========== ルート ==========
class CompanyProfile(BaseModel):
    basic: CompanyBasic = Field(..., description="企業基礎情報")
    financials: Financials = Field(default_factory=Financials, description="財務情報（すべて円）")
    org_signals: List[OrgSignal] = Field(default_factory=list, description="人事・組織動向")
    communications: Communications = Field(default_factory=Communications, description="広報・ソーシャル情報")
    competitors: List[Competitor] = Field(default_factory=list, description="主要競合")
    # 新規フィールド: グループ会社・子会社（上場・非上場を含む）
    group_companies: List[GroupCompany] = Field(
        default_factory=list,
        description="グループ会社・子会社の一覧。上場・非上場を問わず、持株比率や上場情報、簡単な事業要約、根拠URLを含めること。"
    )
    source_url: Optional[str] = Field(None, description="企業全体プロフィールの参照URL")
    last_verified_at: Optional[str] = Field(None, description="全体の最終検証日（YYYY-MM-DD）")
    confidence: Optional[float] = Field(None, ge=0.0, le=1.0, description="全体データの確からしさ (0〜1)")


task = PreparedTask(
    instructions="""
あなたは日本企業の公開情報を調査するアシスタントです。  
入力として与えられる企業名について、Websearchツールを利用して公開情報を調査し、  
指定されたスキーマ（CompanyProfile）に従って構造化JSONを出力してください。  

### 注意事項
- 入力された企業名が複数の企業に該当する場合は、最も有名で代表的な日本企業を優先して調査してください。  
  （例: 「パナソニック」と入力された場合は、家電大手の「パナソニックホールディングス株式会社」を対象とする）  
- ただし、企業名が明確に限定されている場合（例: 「パナソニック インダストリー株式会社」）はその企業を対象にしてください。  

### 調査対象
- 公式コーポレートサイト
- IRページ（決算短信、有価証券報告書、統合報告書）
- TDnet / EDINETの開示情報
- プレスリリース
- 公式SNSアカウント（X, LinkedIn, YouTube, Instagram など）

### 出力ルール
- 金額はすべて「円」に換算して格納してください。IRで百万円・億円単位の数値が出ている場合は必ず換算すること。
- FiscalPeriod には会計年度・四半期・開始日・終了日を可能な限り入力すること。
- FiscalPeriod について、会計年度・四半期別、それぞれ別に取得できる場合は両方取得すること。
- 可能な限り `source_url` を埋めてください。根拠となるページ（IR資料PDF、会社HP、プレスリリース、SNS公式URLなど）。
- 不明な項目は `null` または空リストにしてください。推測や創作は禁止です。
- 財務データは直近3年分の年度決算と最新の四半期決算を含めてください。
- 役員については氏名・役職を最低限含め、判明していれば着任日・退任日も入れてください。
- SNSは公式アカウントのみを対象にしてください。  

### 入力
企業名（例：「トヨタ自動車株式会社」）

### 出力
CompanyProfile モデルに従った構造化JSON。
    """,
    response_format=CompanyProfile,
    api_kwargs={
        "tools": [{"type": "web_search"}],
        "reasoning": {"effort": "medium"}
    }
)



