import React, { useState, useEffect, useRef } from "react";
import { TrendingUp } from "lucide-react";
import { Bar, BarChart, XAxis, YAxis } from "recharts";
import { Button } from "./ui/button";
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "./ui/card";
import { ChartContainer, ChartTooltip, ChartTooltipContent } from "./ui/chart";
import { Table, TableBody, TableCell, TableRow } from "./ui/table";

import img1 from '../assets/img/001.png';
import img2 from '../assets/img/002.png';
import img3 from '../assets/img/003.png';
import img4 from '../assets/img/004.png';
import img5 from '../assets/img/005.png';
import img6 from '../assets/img/006.png';

const styles = `
@media (max-width: 768px) {
    .title {
        font-size: 2.5rem;
    }
    .card {
        flex-direction: column;
        width: 100%;
    }
    .rank-title {
        font-size: 1.5rem;
    }
    .chart-section, .rank-section {
        width: 100%;
        margin-bottom: 20px;
    }
}
@media (max-width: 50%) {
    .card {
        width: 80%;
    }
    .chart-section, .rank-section {
        width: 100%;
    }
}
.slider-container {
    display: flex;
    overflow: hidden;
    width: 100%;
    margin-top: 2rem;
    opacity: 0;
    transition: opacity 0.5s ease-in-out;
}

.slider-container.visible {
    opacity: 1;
}

.slider {
    display: flex;
    transition: transform 0.5s ease-in-out;
}

.slide {
    min-width: 33.33%;
    box-sizing: border-box;
    padding: 0 10px;
}
`;

// 사용자 데이터 타입 정의
interface UserData {
    name: string;
    reaction_count: number;
    join_week: { [week: string]: { [timestamp: string]: { total: number; has_link: boolean; like: object } } };
}

// S3 에서 가져온 데이터 타입 정의
interface ResponseData {
    all_user: number;
    [userId: string]: UserData | string | number;
}

// 게시글 타임스탬프 데이터 타입 정의
interface TimestampData {
    timestamps: { [month: string]: { [timestamp: string]: string } };
    this_month: string;
}

// 차트에 사용할 데이터 타입 정의
interface ChartData {
    name: string;
    count: number;
    fill: string;
}

export function MainChart() {
    const [chartData, setChartData] = useState<ChartData[]>([]);
    const [currentWeek, setCurrentWeek] = useState<string>("ALL");
    const [timestamps, setTimestamps] = useState<{ [key: string]: string }>({});
    const [userData, setUserData] = useState<ResponseData | null>(null);
    const [menuOpen, setMenuOpen] = useState(false); // 메뉴 가시성 상태 추가
    const [animatedTitle, setAnimatedTitle] = useState<string>(""); // 타이틀 애니메이션 상태
    const menuRef = useRef<HTMLDivElement>(null);
    const imageArray = [img1, img2, img3, img4, img5, img6];
    const sliderRef = useRef<HTMLDivElement | null>(null);
    const [isVisible, setIsVisible] = useState(false);
    const [slidesToShow, setSlidesToShow] = useState(3);
    const [currentSlide, setCurrentSlide] = useState(0);
    const [currentMonth, setCurrentMonth] = useState<string>("");

    // 창 크기에 따라 이미지 슬라이드 개수 변경
    useEffect(() => {
        const handleResize = () => {
            if (window.innerWidth < 768) {
                setSlidesToShow(1);
            } else {
                setSlidesToShow(3);
            }
        };

        window.addEventListener('resize', handleResize);

        // 초기 설정
        handleResize();

        return () => {
            window.removeEventListener('resize', handleResize);
        };
    }, []);

    // 데이터 가져온 후 데이터 세팅
    useEffect(() => {
        async function fetchData() {
            try {
                const [userResponse, timestampResponse] = await Promise.all([
                    fetch(`${process.env.REACT_APP_USER_INFO_URL}`),
                    fetch(`${process.env.REACT_APP_TIMESTAMP_URL}`)
                ]);

                const userData: ResponseData = await userResponse.json();
                const timestampData: TimestampData = await timestampResponse.json();

                setUserData(userData);

                const flattenedTimestamps = Object.entries(timestampData.timestamps)
                    .filter(([key]) => key !== 'this_month') // "this_month" 키 제외
                    .reduce((acc, [month, weeks]) => {
                        Object.entries(weeks).forEach(([timestamp, label]) => {
                            acc[timestamp] = label;
                        });
                        return acc;
                    }, {} as { [key: string]: string });

                setTimestamps(flattenedTimestamps);
                setCurrentMonth(timestampData.this_month);

                updateChartData(userData, "ALL");
            } catch (error) {
                console.error("Error fetching data:", error);
            }
        }

        fetchData();
    }, []);

    // 메뉴가 열렸을 때 외부 클릭 시 메뉴 닫기
    useEffect(() => {
        const handleClickOutside = (event: MouseEvent) => {
            if (menuRef.current && !menuRef.current.contains(event.target as Node)) {
                setMenuOpen(false);
            }
        };

        window.addEventListener("mousedown", handleClickOutside);
        return () => {
            window.removeEventListener("mousedown", handleClickOutside);
        };
    }, []);

    // 타이틀 텍스트 애니메이션 적용
    useEffect(() => {
        const fullTitle = "KYOBO TIL CHALLENGE ";
        let index = 0;

        const timer = setInterval(() => {
            setAnimatedTitle((prev) => fullTitle.slice(0, index + 1));
            index++;

            if (index === fullTitle.length) {
                clearInterval(timer);
            }
        }, 100);

        return () => clearInterval(timer);
    }, []);

    // 이미지 슬라이드 변경
    useEffect(() => {
        const interval = setInterval(() => {
            setCurrentSlide((prev) => {
                if (slidesToShow === 1) {
                    // For single image slides, cycle through all images
                    return (prev + 1) % imageArray.length;
                } else {
                    // For 3 images at a time, return to 0 after showing the last set (4, 5, 6)
                    const maxSlides = imageArray.length - slidesToShow;
                    return (prev + slidesToShow) > maxSlides ? 0 : (prev + slidesToShow);
                }
            });
        }, 3500);

        return () => clearInterval(interval);
    }, [slidesToShow, imageArray.length]);

    // 이미지 슬라이드 가시성 설정
    useEffect(() => {
        const observer = new IntersectionObserver(
            (entries) => {
                entries.forEach((entry) => {
                    if (entry.isIntersecting) {
                        setIsVisible(true);
                        observer.disconnect();
                    }
                });
            },
            { threshold: 0.1 }
        );

        if (sliderRef.current) {
            observer.observe(sliderRef.current);
        }

        return () => {
            if (sliderRef.current) {
                observer.unobserve(sliderRef.current);
            }
        };
    }, []);

    // 차트 데이터 업데이트 함수
    const updateChartData = (data: ResponseData, weekKey: string) => {
        let users: ChartData[] = [];
        const chartColors = [
            'var(--chart-1, #003300)',
            'var(--chart-2, #004400)',
            'var(--chart-3, #005500)',
            'var(--chart-4, #006600)',
            'var(--chart-5, #007700)',
            'var(--chart-6, #008800)',
            'var(--chart-7, #009900)',
            'var(--chart-8, #00aa00)',
            'var(--chart-9, #00bb00)',
            'var(--chart-10, #00cc00)',
            'var(--chart-11, #00dd00)',
            'var(--chart-12, #00ee00)',
            'var(--chart-13, #00ff00)',
            'var(--chart-14, #33ff33)',
            'var(--chart-15, #66ff66)',
            'var(--chart-16, #99ff99)',
            'var(--chart-17, #ccffcc)',
            'var(--chart-18, #e6ffe6)',
            'var(--chart-19, #f2fff2)',
            'var(--chart-20, #fafffa)',
        ];

        const currentMonth = timestamps.this_month;

        if (weekKey === "ALL") {
            users = Object.entries(data)
                .filter(([key, value]) => typeof value === "object" && value !== null && 'name' in value)
                .map(([userId, userInfo]) => ({
                    name: (userInfo as UserData).name,
                    count: (userInfo as UserData).reaction_count,
                }))
                .filter((user) => user.count > 0)
                .sort((a, b) => b.count - a.count) // 먼저 정렬
                .map((user, index) => ({
                    ...user,
                    fill: chartColors[index % chartColors.length], // 그라데이션 순서대로 색상 할당
                }));
        } else {
            users = Object.entries(data)
                .filter(([key, value]) => typeof value === "object" && value !== null && 'name' in value)
                .map(([userId, userInfo]) => {
                    const joinWeek = (userInfo as UserData).join_week;
                    const weekData = joinWeek[weekKey];

                    if (!weekData) return null;

                    const total = Object.entries(weekData)
                        .filter(([, entry]) => entry.has_link)
                        .reduce((sum, [, entry]) => sum + entry.total, 0);

                    return total > 0 ? {
                        name: (userInfo as UserData).name,
                        count: total,
                    } : null;
                })
                .filter((user): user is ChartData => user !== null)
                .sort((a, b) => b.count - a.count) // 먼저 정렬
                .map((user, index) => ({
                    ...user,
                    fill: chartColors[index % chartColors.length], // 그라데이션 순서대로 색상 할당
                }));
        }

        setChartData(users);
    };

    // 참여 주차 반환 함수
    const getParticipationWeeks = (user: UserData) => {
        return Object.entries(user.join_week)
            .filter(([week, entries]) =>
                Object.values(entries).some(entry => entry.has_link && entry.total > 0)
            )
            .map(([week]) => timestamps[week])
            .join(", ");
    };

    // chartConfig 정의
    const chartConfig = {
        reactionCount: {
            label: "Reaction Count",
        },
    };

    return (
        <div className="mx-8 mt-10" style={{position: 'relative', overflow: 'visible'}}>
            <style>{styles}</style>
            {/* 제목 */}
            <h1 className="title text-7xl font-bold text-center mb-6" style={{color: '#474baa'}}>
                {animatedTitle.split(' ')[0].startsWith("KYOBO") ? (
                    <span style={{color: '#4dac27'}}>
                        {animatedTitle.split(' ')[0]}
                    </span>
                ) : (
                    animatedTitle.split(' ')[0]
                )}{" "}
                {animatedTitle.split(' ').slice(1).join(' ')}
                {/*{animatedTitle.slice(2)} {/* '교보'를 제외한 나머지 부분 */}
                🏆
            </h1>
            <div className="relative">
                <div className="flex justify-between items-center mb-4">
                    {/* 메뉴 버튼 */}
                    <Button
                        onClick={() => setMenuOpen(!menuOpen)}
                        style={{
                            border: '1px solid #d1d5db',
                            borderRadius: '10px',
                            padding: '10px 20px'
                        }}
                    >
                        다른 주차
                    </Button>
                    {/* 메뉴가 열렸을 때 표시되는 메뉴 항목 */}
                    {menuOpen && (
                        <div ref={menuRef}
                             className="absolute top-full left-0 mt-2 bg-white border border-gray-300 rounded-2xl shadow-lg"
                             style={{zIndex: 1000}}>
                            <Button
                                onClick={() => {
                                    setCurrentWeek("ALL");
                                    setMenuOpen(false);
                                    if (userData) updateChartData(userData, "ALL");
                                }}
                                style={currentWeek === "ALL" ? {
                                    backgroundColor: 'black',
                                    color: 'white',
                                    borderRadius: '10px'
                                } : {borderRadius: '10px'}}
                                className="block w-full text-left px-4 py-2"
                            >
                                ALL
                            </Button>
                            {Object.entries(timestamps).map(([timestamp, label]) => (
                                <Button
                                    key={timestamp}
                                    onClick={() => {
                                        setCurrentWeek(label.toString());
                                        setMenuOpen(false); // 메뉴 닫기
                                        if (userData) updateChartData(userData, timestamp);
                                    }}
                                    style={currentWeek === label.toString() ? {
                                        backgroundColor: 'black',
                                        color: 'white',
                                        borderRadius: '10px'
                                    } : {borderRadius: '10px'}}
                                    className="block w-full text-left px-4 py-2"
                                >
                                    {label.toString()}
                                </Button>
                            ))}
                        </div>
                    )}
                </div>
            </div>
            <Card className="card flex flex-row flex-1" style={{overflow: 'visible'}}>
                {/* 차트 섹션 */}
                <div className="chart-section hidden sm:block w-1/2 md:w-2/3 border-r border-gray-300">
                    <CardHeader>
                        <CardTitle className="font-bold">TIL CHALLENGE CHART</CardTitle>
                        <CardDescription>{currentWeek}</CardDescription>
                    </CardHeader>
                    <CardContent className="flex-1">
                        <ChartContainer config={chartConfig}>
                            <BarChart
                                accessibilityLayer
                                data={chartData}
                                layout="vertical"
                                margin={{left: 0}}
                                barCategoryGap="0%"
                            >
                                <YAxis
                                    dataKey="name"
                                    type="category"
                                    tickLine={false}
                                    tickMargin={10}
                                    axisLine={false}
                                    tick={{fontSize: 13}}
                                />
                                <XAxis dataKey="count" type="number" hide/>
                                <ChartTooltip
                                    cursor={false}
                                    content={<ChartTooltipContent hideLabel/>}
                                />
                                <Bar
                                    dataKey="count"
                                    layout="vertical"
                                    radius={5}
                                    barSize={30}
                                    minPointSize={1}
                                />
                            </BarChart>
                        </ChartContainer>
                    </CardContent>
                    <CardFooter className="flex-col items-start gap-2 text-sm">
                        <div className="flex gap-2 font-medium leading-none">
                            교보 CDA - TIL CHALLENGE <TrendingUp className="h-4 w-4"/>
                        </div>
                    </CardFooter>
                </div>

                {/* 순위 테이블 */}
                <CardContent className="rank-section flex-1 w-full sm:w-1/2 md:w-1/3" style={{overflow: 'visible'}}>
                    <h1 className="rank-title mb-2 mt-7 text-xl md:text-xl">RANK</h1>
                    <Table className="w-full">
                        <TableBody>
                            {chartData.map((user, index) => {
                                const userInfo = userData && Object.values(userData).find(
                                    (info) => typeof info === "object" && (info as UserData).name === user.name
                                ) as UserData | undefined;

                                return (
                                    <TableRow key={user.name}>
                                        <TableCell className="py-4 text-base font-bold">
                                            <span style={{fontSize: '2.0em', lineHeight: '1'}}>
                                                {index === 0 ? '🥇' : index === 1 ? '🥈' : index === 2 ? '🥉' : ''}
                                            </span>
                                            {index >= 3 && <span>{index + 1}</span>}
                                        </TableCell>
                                        <TableCell className="text-base font-semibold">
                                            {/*<UserToolTip content={`Weeks: ${userInfo ? getParticipationWeeks(userInfo) : "No participation"}`}>*/}
                                            {user.name}
                                            {/*</UserToolTip>*/}
                                        </TableCell>
                                        <TableCell className="text-right">
                                <span
                                    className="inline-flex items-center justify-center w-12 h-8 rounded-2xl bg-gray-200 text-sm">
                                    👍 {user.count}
                                </span>
                                        </TableCell>
                                    </TableRow>
                                );
                            })}
                        </TableBody>
                    </Table>
                </CardContent>
                {/* 모바일 화면에서 차트를 아래에 표시 */}
                <div className="chart-section sm:hidden w-full border-t border-gray-300">
                    <CardHeader>
                        <CardTitle className="font-bold">TIL CHALLENGE CHART</CardTitle>
                        <CardDescription>{currentWeek}</CardDescription>
                    </CardHeader>
                    <CardContent className="flex-1">
                        <ChartContainer config={chartConfig}>
                            <BarChart
                                accessibilityLayer
                                data={chartData}
                                layout="vertical"
                                margin={{left: 0}}
                                barCategoryGap="0%"
                            >
                                <YAxis
                                    dataKey="name"
                                    type="category"
                                    tickLine={false}
                                    tickMargin={10}
                                    axisLine={false}
                                    tick={{fontSize: 5}}
                                />
                                <XAxis dataKey="count" type="number" hide/>
                                <ChartTooltip
                                    cursor={false}
                                    content={<ChartTooltipContent hideLabel/>}
                                />
                                <Bar
                                    dataKey="count"
                                    layout="vertical"
                                    radius={5}
                                    barSize={30}
                                    minPointSize={1}
                                />
                            </BarChart>
                        </ChartContainer>
                    </CardContent>
                    <CardFooter className="flex-col items-start gap-2 text-sm">
                        <div className="flex gap-2 font-medium leading-none">
                            교보 CDA - TIL CHALLENGE <TrendingUp className="h-4 w-4"/>
                        </div>
                    </CardFooter>
                </div>
            </Card>
            <div ref={sliderRef} className={`slider-container ${isVisible ? 'visible' : ''}`}>
                <div
                    className="slider"
                    style={{transform: `translateX(-${currentSlide * (100 / slidesToShow)}%)`}}
                >
                    {imageArray.map((image, index) => (
                        <div key={index} className="slide" style={{flex: `0 0 ${100 / slidesToShow}%`}}>
                            <img src={image} alt={`Slide ${index + 1}`} style={{width: '100%', height: 'auto'}}/>
                        </div>
                    ))}
                </div>
            </div>
            <footer className="text-gray-400 text-center py-6 mt-10">
                <p className="text-xxs md:text-base">&copy; 2024 고진혁. All rights reserved.</p>
                <p className="text-xxs md:text-base">해당 서비스는 2024년 12월 3일에 종료될 예정입니다.</p>
            </footer>
        </div>
    );
}